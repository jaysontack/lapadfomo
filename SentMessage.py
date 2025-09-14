import os
import asyncio
import random
import re
import json
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji

GIFS_DIR = "gifs"

groups = ["Lets_Announcepad"]
target_channel = "https://t.me/lapad_announcement"

# ENV’den JSON olarak accounts okuma (Render için tek değişken kullanmak kolay olur)
accounts = json.loads(os.getenv("ACCOUNTS_JSON", "[]"))

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
                await asyncio.sleep(random.randint(20, 40))
            await asyncio.sleep(random.randint(600, 1200))

    client.loop.create_task(general_chat_loop())
    client.loop.create_task(conversation_loop())
    return client


async def main():
    clients = []
    for idx, acc in enumerate(accounts, start=1):
        client = TelegramClient(StringSession(acc["STRING_SESSION"]), acc["API_ID"], acc["API_HASH"])
        await client.start()
        clients.append(client)

    for idx, client in enumerate(clients, start=1):
        if client:
            asyncio.create_task(client_worker(idx, accounts[idx-1], client, clients))
            await asyncio.sleep(10)

    await asyncio.gather(*(c.run_until_disconnected() for c in clients if c))


if __name__ == "__main__":
    asyncio.run(main())
