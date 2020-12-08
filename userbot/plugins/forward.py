# ported from paperplaneExtended by avinashreddy3108 for media support
import re

from telethon import events

from .. import BOTLOG_CHATID, CMD_HELP, bot
from ..utils import admin_cmd, edit_or_reply, sudo_cmd
from .sql_helper.filter_sql import (
    add_filter,
    get_filters,
    remove_all_filters,
    remove_filter,
)


@bot.on(events.NewMessage(incoming=True))
async def filter_incoming_handler(handler):
    try:
        if not (await handler.get_sender()).bot:
            name = handler.raw_text
            filters = get_filters(handler.chat_id)
            if not filters:
                return
            for trigger in filters:
                pattern = r"( |^|[^\w])" + re.escape(trigger.keyword) + r"( |$|[^\w])"
                if re.search(pattern, name, flags=re.IGNORECASE):
                    if trigger.f_mesg_id:
                        msg_o = await handler.client.get_messages(
                            entity=BOTLOG_CHATID, ids=int(trigger.f_mesg_id)
                        )
                        await handler.reply(msg_o.message, file=msg_o.media)
                    elif trigger.reply:
                        await handler.reply(trigger.reply)
    except AttributeError:
        pass


@bot.on(admin_cmd(pattern="filter (.*)"))
@bot.on(sudo_cmd(pattern="filter (.*)", allow_sudo=True))
async def add_new_filter(new_handler):
    keyword = new_handler.pattern_match.group(1)
    string = new_handler.text.partition(keyword)[2]
    msg = await new_handler.get_reply_message()
    msg_id = None
    if msg and msg.media and not string:
        if BOTLOG_CHATID:
            await new_handler.client.send_message(
                BOTLOG_CHATID,
                f"#FILTER\
            \nCHAT ID: {new_handler.chat_id}\
            \nTRIGGER: {keyword}\
            \n\nThe following message is saved as the filter's reply data for the chat, please do NOT delete it !!",
            )
            msg_o = await new_handler.client.forward_messages(
                entity=BOTLOG_CHATID,
                messages=msg,
                from_peer=new_handler.chat_id,
                silent=True,
            )
            msg_id = msg_o.id
        else:
            await edit_or_reply(
                new_handler,
                "`Saving media as reply to the filter requires the BOTLOG_CHATID to be set.`",
            )
            return
    elif new_handler.reply_to_msg_id and not string:
        rep_msg = await new_handler.get_reply_message()
        string = rep_msg.text
    success = "`Filter` **{}** `{} ditambahkan`"
    if add_filter(str(new_handler.chat_id), keyword, string, msg_id) is True:
        return await edit_or_reply(new_handler, success.format(keyword, "berhasil"))
    remove_filter(str(new_handler.chat_id), keyword)
    if add_filter(str(new_handler.chat_id), keyword, string, msg_id) is True:
        return await edit_or_reply(new_handler, success.format(keyword, "Updated"))
    await edit_or_reply(new_handler, f"Error while setting filter for {keyword}")


@bot.on(admin_cmd(pattern="filters$"))
@bot.on(sudo_cmd(pattern="filters$", allow_sudo=True))
async def on_snip_list(event):
    OUT_STR = "tidak ada filter pada pesan ini."
    filters = get_filters(event.chat_id)
    for filt in filters:
        if OUT_STR == "Tidak ada filter di chat ini.":
            OUT_STR = "Filter di chat ini:\n"
        OUT_STR += "👉 `{}`\n".format(filt.keyword)
    if len(OUT_STR) > 4096:
        with io.BytesIO(str.encode(OUT_STR)) as out_file:
            out_file.name = "filters.text"
            await bot.send_file(
                event.chat_id,
                out_file,
                force_document=True,
                allow_cache=False,
                caption="Filter yang tersedia di chat ini",
                reply_to=event,
            )
            await event.delete()
    else:
        await edit_or_reply(event, OUT_STR)


@bot.on(admin_cmd(pattern="stop (.*)"))
@bot.on(sudo_cmd(pattern="stop (.*)", allow_sudo=True))
