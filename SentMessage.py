import os
import asyncio
import random
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji

SESSIONS_DIR = "sessions"
GIFS_DIR = "gifs"

groups = ["Lets_Announcepad"]
target_channel = "https://t.me/lapad_announcement"

accounts = [
    {"API_ID": 21318086, "API_HASH": "527a5add32472c5a8ef2ce5fe9b33e41"},
    {"API_ID": 27534424, "API_HASH": "0177e8fb2ce88955502a06063ea843e7"},
    {"API_ID": 23335629, "API_HASH": "cced31cf5ea9f486336dea367c2a7deb"},
    {"API_ID": 11296099, "API_HASH": "aff2e88e5babf3f8808b4612c92dd617"},
    {"API_ID": 25585876, "API_HASH": "1b85474d2cd05da895f5c5d53bce8654"},
    {"API_ID": 20842385, "API_HASH": "c38c95c2b5b3886e19f1ff2cbbb3a8c5"},
    {"API_ID": 23058473, "API_HASH": "a435ac06f42f7d563e04774cfe4a568e"},
    {"API_ID": 24813233, "API_HASH": "222d6d129400decc4938c35980b1b7cf"},
    {"API_ID": 27506052, "API_HASH": "7296b71b61e1d74c3f083019b0b84b42"},
    {"API_ID": 28799463, "API_HASH": "96585faba9c39035d19993edd4682bda"},
    {"API_ID": 24537749, "API_HASH": "f6a7168b8a96adb0a3009ac0de260973"},
    {"API_ID": 29542269, "API_HASH": "76cd0de7e80f5bd96299d3fa2e89de0c"},
    {"API_ID": 29438496, "API_HASH": "7e03d59872e8b6b21df43d4214cb8694"},
    {"API_ID": 29039352, "API_HASH": "281e724ac1729dd817a4a8537d7078cd"},
    {"API_ID": 25330921, "API_HASH": "c3e7cf340e6ddb7c3816b709d4bbe1b2"},
    {"API_ID": 22639266, "API_HASH": "9606c5dfaf2077182d8cd7f7f75feead"},
    {"API_ID": 11514098, "API_HASH": "2a8c4381ac25158bfece8f45f868ee1b"},
    {"API_ID": 28274427, "API_HASH": "9dd2cc7935d53e9ede4d85a3c07d861f"},
    {"API_ID": 25331942, "API_HASH": "6fe593cb4d69a7f106efd84f0455b9b0"},
    {"API_ID": 20300289, "API_HASH": "fe3aad03905f985e9fdb68566d4d6649"},
    {"API_ID": 22284524, "API_HASH": "a7f551e138441fe602427c9115a9c742"},
]

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
    me = await client.get_me()
    print(f"👤 {me.first_name} (@{me.username}) aktif oldu ve kanal dinlemede...")

    @client.on(events.NewMessage(chats=target_channel))
    async def handler(event):
        try:
            chosen = random.sample(emojis, 2)
            for emoji in chosen:
                await client(SendReactionRequest(
                    peer=event.chat_id,
                    msg_id=event.id,
                    reaction=[ReactionEmoji(emoticon=emoji)]
                ))
                print(f"💬 {me.username} reaction bıraktı: {emoji}")
                await asyncio.sleep(2)
        except Exception as e:
            print(f"⚠️ Reaction hatası: {e}")

        text = event.raw_text
        match = re.search(r"#lapad\s+(#[A-Za-z0-9_]+)", text, re.IGNORECASE)
        if not match:
            return
        symbol = match.group(1).replace("#", "").upper()
        print(f"🔎 Symbol bulundu: {symbol}")

        hype = random.choice(messages).replace("{symbol}", symbol)

        gifs = os.listdir(GIFS_DIR) if os.path.exists(GIFS_DIR) else []
        gif_path = os.path.join(GIFS_DIR, random.choice(gifs)) if gifs else None

        for g in groups:
            try:
                await client(JoinChannelRequest(g))
                sent = await client.send_message(g, hype)
                print(f"✅ {me.username} gruba hype mesajı attı: {hype}")
                await asyncio.sleep(2)

                if stickers:
                    sticker = random.choice(stickers)
                    await client.send_file(g, sticker, reply_to=sent.id)
                    print(f"🎨 {me.username} gruba sticker attı")

                if gif_path and random.random() < 0.4:
                    await client.send_file(g, gif_path, reply_to=sent.id)
                    print(f"🎞️ {me.username} gruba gif attı: {os.path.basename(gif_path)}")

                if "Twitter" in text or "Telegram" in text:
                    block = random.choice(conversations)
                    print(f"🗨️ Yeni conversation başladı (Twitter/Telegram tetikledi)...")
                    last_msg = sent
                    prev_sender = None
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
                            # flood önleme: aynı kullanıcı üst üste gelirse farklı client seç
                            if sender == prev_sender:
                                sender_idx = (sender_idx + 1) % len(clients)
                            sender_client = clients[sender_idx]
                        except (ValueError, IndexError):
                            print(f"⚠️ {sender} için client bulunamadı")
                            continue
                        try:
                            if last_msg:
                                sent = await sender_client.send_message(g, content, reply_to=last_msg.id)
                                print(f"💬 {sender} replied in {g}: {content}")
                            else:
                                sent = await sender_client.send_message(g, content)
                                print(f"💬 {sender} said in {g}: {content}")
                            last_msg = sent
                            prev_sender = sender
                        except Exception as e:
                            print(f"⚠️ Conversation hatası: {e}")
                        await asyncio.sleep(random.randint(20, 40))  # süre artırıldı
            except Exception as e:
                print(f"⚠️ Grup mesaj hatası: {e}")

    async def general_chat_loop():
        while True:
            msg = random.choice(general_msgs) if general_msgs else "🔥 Bullish vibes!"
            gifs = os.listdir(GIFS_DIR) if os.path.exists(GIFS_DIR) else []
            gif_path = os.path.join(GIFS_DIR, random.choice(gifs)) if gifs else None

            for g in groups:
                try:
                    sent = await client.send_message(g, msg)
                    print(f"💬 {me.username} genel mesaj attı: {msg}")
                    await asyncio.sleep(2)

                    if stickers:
                        sticker = random.choice(stickers)
                        await client.send_file(g, sticker, reply_to=sent.id)
                        print(f"🎨 {me.username} genel sticker attı")

                    if gif_path and random.random() < 0.4:
                        await client.send_file(g, gif_path, reply_to=sent.id)
                        print(f"🎞️ {me.username} genel gif attı: {os.path.basename(gif_path)}")
                except Exception as e:
                    print(f"⚠️ Genel sohbet hatası: {e}")

            await asyncio.sleep(random.randint(300, 600))

    async def conversation_loop():
        while True:
            block = random.choice(conversations)
            print(f"🗨️ Yeni conversation başladı (otomatik)...")
            last_msg = None
            prev_sender = None
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
                    # flood önleme: aynı kullanıcı üst üste gelirse farklı client seç
                    if sender == prev_sender:
                        sender_idx = (sender_idx + 1) % len(clients)
                    sender_client = clients[sender_idx]
                except (ValueError, IndexError):
                    print(f"⚠️ {sender} için client bulunamadı")
                    continue
                for g in groups:
                    try:
                        if last_msg:
                            sent = await sender_client.send_message(g, content, reply_to=last_msg.id)
                            print(f"💬 {sender} replied in {g}: {content}")
                        else:
                            sent = await sender_client.send_message(g, content)
                            print(f"💬 {sender} said in {g}: {content}")
                        last_msg = sent
                        prev_sender = sender
                    except Exception as e:
                        print(f"⚠️ Conversation hatası: {e}")
                await asyncio.sleep(random.randint(20, 40))  # süre artırıldı
            await asyncio.sleep(random.randint(600, 1200))

    client.loop.create_task(general_chat_loop())
    client.loop.create_task(conversation_loop())
    return client


async def main():
    clients = []
    for idx, acc in enumerate(accounts, start=1):
        session_file = os.path.join(SESSIONS_DIR, f"session{idx}.session")
        if not os.path.exists(session_file):
            print(f"⚠️ {session_file} bulunamadı, atlanıyor.")
            clients.append(None)
            continue
        with open(session_file, "r") as f:
            session_str = f.read().strip()
        client = TelegramClient(StringSession(session_str), acc["API_ID"], acc["API_HASH"])
        await client.start()
        clients.append(client)

    for idx, client in enumerate(clients, start=1):
        if client:
            asyncio.create_task(client_worker(idx, accounts[idx-1], client, clients))
            await asyncio.sleep(10)

    await asyncio.gather(*(c.run_until_disconnected() for c in clients if c))


if __name__ == "__main__":
    asyncio.run(main())