import os
import asyncio
import random
import json
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji
from telethon.errors import AuthKeyDuplicatedError

groups = ["Lets_Announcepad"]
target_channel = "https://t.me/lapad_announcement"
processing_lock = asyncio.Lock()

accounts = []
raw_accounts = os.getenv("ACCOUNTS_JSON")
if raw_accounts:
    try:
        accounts = json.loads(raw_accounts)
        print(f"✅ ACCOUNTS_JSON loaded: {len(accounts)} accounts")
    except Exception as e:
        print(f"⚠️ ACCOUNTS_JSON parse error: {e}")

if not accounts:
    idx = 1
    while True:
        api_id = os.getenv(f"API_ID_{idx}")
        api_hash = os.getenv(f"API_HASH_{idx}")
        session = os.getenv(f"SESSION_{idx}")
        if not api_id or not api_hash or not session:
            break
        accounts.append({
            "API_ID": int(api_id),
            "API_HASH": api_hash,
            "STRING_SESSION": session
        })
        idx += 1
    print(f"✅ Loaded {len(accounts)} accounts from ENV")

if not accounts:
    print("❌ No accounts found, exiting...")
    exit(1)

emojis = ["🔥", "🚀", "❤️", "😂", "😎", "👏", "🎉", "💯"]

with open("message.txt", "r", encoding="utf-8") as f:
    messages = [line.strip() for line in f if line.strip()]

with open("general.txt", "r", encoding="utf-8") as f:
    general_msgs = [line.strip() for line in f if line.strip()]

with open("stickers.txt", "r", encoding="utf-8") as f:
    stickers = [line.strip() for line in f if line.strip()]

with open("conversations.txt", "r", encoding="utf-8") as f:
    raw_blocks = f.read().split("---")
conversations = [block.strip().splitlines() for block in raw_blocks if block.strip()]


async def client_worker(idx, acc, client, clients):
    try:
        me = await client.get_me()
        print(f"👤 Account {idx} active: {me.first_name} (@{me.username})")
    except Exception as e:
        print(f"❌ Account {idx} info error: {e}")
        return

    @client.on(events.NewMessage(chats=target_channel))
    async def handler(event):
        if processing_lock.locked():
            print("⏳ Another post is being processed, ignoring this one.")
            return

        async with processing_lock:
            text = event.raw_text
            print(f"📩 {me.username} saw new post: {text[:60]}...")

            try:
                for c in clients:
                    if not c:
                        continue
                    me2 = await c.get_me()
                    for round_num in range(random.randint(2, 3)):
                        emoji = random.choice(emojis)
                        await c(SendReactionRequest(
                            peer=event.chat_id,
                            msg_id=event.id,
                            reaction=[ReactionEmoji(emoticon=emoji)]
                        ))
                        print(f"💬 {me2.username} reacted with {emoji}")
                        await asyncio.sleep(1)
            except Exception as e:
                print(f"⚠️ Reaction error: {e}")

            msg_txt = random.choice(messages) if messages else "🔥 HODL!"

            for idx2, c in enumerate(clients):
                if not c:
                    continue
                try:
                    me2 = await c.get_me()
                    if idx2 == 0:
                        await c.send_message(groups[0], msg_txt, reply_to=event.id)
                        print(f"👤 {me2.username} (1) sent message")
                    elif idx2 == 1:
                        sent = await c.send_message(groups[0], msg_txt, reply_to=event.id)
                        if stickers:
                            sticker = random.choice(stickers)
                            await c.send_file(groups[0], sticker, reply_to=sent.id)
                        print(f"👤 {me2.username} (2) sent message + sticker")
                    elif idx2 == 2:
                        sent = await c.send_message(groups[0], msg_txt, reply_to=event.id)
                        await asyncio.sleep(2)
                        await c.send_message(groups[0], f"Re: {msg_txt}", reply_to=sent.id)
                        print(f"👤 {me2.username} (3) sent message + reply")
                    else:
                        await c.send_message(groups[0], msg_txt, reply_to=event.id)
                        print(f"👤 {me2.username} ({idx2+1}) sent message")

                    await asyncio.sleep(random.randint(3, 6))
                except Exception as e:
                    print(f"⚠️ Account {idx2+1} task error: {e}")

            print("✅ All accounts finished, waiting for next post...")

    return client


async def general_chat_loop(clients, accounts):
    print("🔄 General chat loop started")
    while True:
        for idx, client in enumerate(clients):
            if not client:
                continue
            try:
                me = await client.get_me()
            except Exception as e:
                print(f"⚠️ {idx+1} get_me error: {e}")
                continue

            msg = random.choice(general_msgs) if general_msgs else "🔥 Bullish vibes!"
            for g in groups:
                try:
                    sent = await client.send_message(g, msg)
                    print(f"💬 {me.username} ({idx+1}) sent general msg: {msg}")
                    await asyncio.sleep(2)

                    if stickers:
                        sticker = random.choice(stickers)
                        await client.send_file(g, sticker, reply_to=sent.id)
                        print(f"🎨 {me.username} ({idx+1}) sent sticker")
                        await asyncio.sleep(2)

                except Exception as e:
                    print(f"⚠️ General chat error ({me.username}): {e}")

        print("⏳ All accounts sent messages + stickers, sleeping...")
        await asyncio.sleep(random.randint(200, 300))


async def conversation_loop(clients, accounts):
    print("🔄 Conversation loop started")
    while True:
        block = random.choice(conversations)
        print("🗨️ New conversation started")
        last_msg, prev_sender = None, None
        for line in block:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "->" in line:
                speaker, content = line.split(":", 1)
                sender, _ = speaker.split("->")
                sender = sender.strip()
            else:
                sender, content = line.split(":", 1)
                sender = sender.strip()
            content = content.strip()
            try:
                sender_idx = "ABCD".index(sender)
                if sender == prev_sender:
                    sender_idx = (sender_idx + 1) % len(clients)
                sender_client = clients[sender_idx]
                if not sender_client:
                    print(f"⚠️ No client for {sender}, skipping...")
                    continue
                me = await sender_client.get_me()
            except (ValueError, IndexError) as e:
                print(f"⚠️ Index error for {sender}: {e}")
                continue
            for g in groups:
                try:
                    if last_msg:
                        sent = await sender_client.send_message(g, content, reply_to=last_msg.id)
                        print(f"💬 {sender} ({me.username}) replied in {g}: {content}")
                    else:
                        sent = await sender_client.send_message(g, content)
                        print(f"💬 {sender} ({me.username}) said in {g}: {content}")
                    last_msg, prev_sender = sent, sender
                except Exception as e:
                    print(f"⚠️ Conversation error ({me.username}): {e}")
            await asyncio.sleep(random.randint(20, 40))
        await asyncio.sleep(random.randint(100, 200))


async def main():
    clients = []
    for idx, acc in enumerate(accounts, start=1):
        print(f"🚀 Starting account {idx}... API_ID={acc['API_ID']}")
        try:
            client = TelegramClient(
                StringSession(acc["STRING_SESSION"]),
                acc["API_ID"],
                acc["API_HASH"]
            )
            await client.start()
            clients.append(client)
            print(f"✅ Account {idx} logged in")
        except AuthKeyDuplicatedError:
            print(f"❌ Account {idx} invalid (AuthKeyDuplicatedError), skipped")
            clients.append(None)
        except Exception as e:
            print(f"❌ Account {idx} failed: {e}")
            clients.append(None)

    active = [c for c in clients if c]
    print(f"✅ {len(active)} clients active, {len(clients)-len(active)} failed")

    for idx, client in enumerate(clients, start=1):
        if client:
            print(f"▶️ Starting client_worker: {idx}")
            asyncio.create_task(client_worker(idx, accounts[idx-1], client, clients))
            await asyncio.sleep(2)

    if not active:
        print("❌ No clients active, exiting...")
        return

    asyncio.create_task(general_chat_loop(active, accounts))
    asyncio.create_task(conversation_loop(active, accounts))

    try:
        await asyncio.gather(*(c.run_until_disconnected() for c in active))
    finally:
        for client in active:
            await client.disconnect()
        print("🛑 All clients disconnected.")


if __name__ == "__main__":
    print("🔥 Bot starting...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Manual stop.")
