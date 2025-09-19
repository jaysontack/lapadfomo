import os
import asyncio
import random
import json
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji
from telethon.errors import AuthKeyDuplicatedError

groups = ["Lets_Announcepad"]  # mesaj + sticker buraya
target_channel = "https://t.me/lapad_announcement"  # sadece reaction buraya

# --------------------------
# ✅ ENV’den hesapları oku
# --------------------------
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
        session = os.getenv(f"SESSION_{idx}") or os.getenv(f"STRING_SESSION_{idx}")
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

# --------------------------
# ✅ Diğer ayarlar
# --------------------------
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


# ✅ Çok kelimeli token ismini yakalar
def extract_token_name(text: str) -> str:
    words = text.split()
    collected = []
    for w in words:
        if w.lower() in ["is", "are"]:
            break
        if w.replace("-", "").replace("_", "").isalpha():
            collected.append(w)
    return " ".join(collected) if collected else "Token"


# ✅ Kanal postu geldiğinde tüm hesaplar sırayla görev yapar
async def handle_new_post(event, clients):
    token_name = extract_token_name(event.raw_text)
    print(f"📢 New post detected, token: {token_name}")

    for idx, client in enumerate(clients, start=1):
        if not client:
            continue
        try:
            me = await client.get_me()

            # Reaction (kanala)
            emoji = emojis[(idx - 1) % len(emojis)]
            await client(SendReactionRequest(
                peer=event.chat_id,
                msg_id=event.id,
                reaction=[ReactionEmoji(emoticon=emoji)]
            ))
            print(f"💬 {me.username} reacted {emoji}")
            await asyncio.sleep(2)

            # Mesaj (gruba)
            msg_txt = random.choice(messages).replace("{name}", token_name)
            sent = await client.send_message(groups[0], msg_txt)
            print(f"💬 {me.username} sent msg: {msg_txt}")
            await asyncio.sleep(random.randint(3, 6))

            # Sticker (gruba)
            if stickers:
                sticker = random.choice(stickers)
                await client.send_file(groups[0], sticker, reply_to=sent.id)
                print(f"🎨 {me.username} sent sticker")
            await asyncio.sleep(random.randint(4, 8))

        except Exception as e:
            print(f"⚠️ Error with {me.username}: {e}")


# ✅ General chat loop
async def general_chat_loop(clients, accounts):
    print("🔄 General chat loop started")
    while True:
        for idx, client in enumerate(clients):
            if not client:
                continue
            try:
                me = await client.get_me()
            except Exception as e:
                print(f"⚠️ {idx+1}. get_me error: {e}")
                continue

            for g in groups:
                try:
                    msg = random.choice(general_msgs) if general_msgs else "🔥 Bullish vibes!"
                    sent = await client.send_message(g, msg)
                    print(f"💬 {me.username} ({idx+1}) general msg: {msg}")
                    await asyncio.sleep(random.randint(3, 7))

                    if stickers:
                        sticker = random.choice(stickers)
                        await client.send_file(g, sticker, reply_to=sent.id)
                        print(f"🎨 {me.username} ({idx+1}) sticker sent")
                    await asyncio.sleep(random.randint(5, 10))

                except Exception as e:
                    print(f"⚠️ General chat error ({me.username}): {e}")

        print("⏳ Waiting before next general round...")
        await asyncio.sleep(random.randint(200, 300))


# ✅ Conversation loop
async def conversation_loop(clients, accounts):
    print("🔄 Conversation loop started")
    while True:
        block = random.choice(conversations)
        print(f"🗨️ New conversation started...")
        last_msg, prev_sender = None, None
        for line in block:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
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
                print(f"⚠️ Sender index error: {e}")
                continue
            for g in groups:
                try:
                    sent = await sender_client.send_message(g, content)
                    print(f"💬 {sender} ({me.username}) said in {g}: {content}")
                    last_msg, prev_sender = sent, sender
                except Exception as e:
                    print(f"⚠️ Conversation error ({me.username}): {e}")
            await asyncio.sleep(random.randint(20, 40))
        await asyncio.sleep(random.randint(100, 200))


# ✅ Ana fonksiyon
async def main():
    clients = []
    for idx, acc in enumerate(accounts, start=1):
        print(f"🚀 Starting account {idx}...")
        try:
            client = TelegramClient(
                StringSession(acc["STRING_SESSION"]),
                acc["API_ID"],
                acc["API_HASH"]
            )
            await client.start()
            clients.append(client)
            print(f"✅ Account {idx} started successfully")
        except AuthKeyDuplicatedError:
            print(f"❌ Account {idx} invalid (AuthKeyDuplicatedError), skipping...")
            clients.append(None)
        except Exception as e:
            print(f"❌ Account {idx} failed to start: {e}")
            clients.append(None)

    active = [c for c in clients if c]
    print(f"✅ {len(active)} clients active, {len(clients)-len(active)} failed")

    if not active:
        print("❌ No active clients, exiting...")
        return

    @active[0].on(events.NewMessage(chats=target_channel))
    async def global_handler(event):
        await handle_new_post(event, active)

    asyncio.create_task(general_chat_loop(active, accounts))
    asyncio.create_task(conversation_loop(active, accounts))

    try:
        await asyncio.gather(*(c.run_until_disconnected() for c in active))
    finally:
        for client in active:
            await client.disconnect()
        print("🛑 All clients stopped.")


if __name__ == "__main__":
    print("🔥 Bot starting...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Stopped manually.")
