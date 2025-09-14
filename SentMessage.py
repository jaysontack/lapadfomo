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

# 1) Öncelik: Tek bir JSON (ACCOUNTS_JSON)
accounts = []
raw_accounts = os.getenv("ACCOUNTS_JSON")
if raw_accounts:
    try:
        accounts = json.loads(raw_accounts)
        print(f"✅ ACCOUNTS_JSON bulundu: {len(accounts)} hesap yüklendi")
    except Exception as e:
        print(f"⚠️ ACCOUNTS_JSON parse hatası: {e}")

# 2) Eğer JSON yoksa: API_ID_1, API_HASH_1, SESSION_1 formatından oku
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
    print(f"✅ ENV formatından {len(accounts)} hesap yüklendi")

if not accounts:
    print("❌ Hiç hesap bulunamadı, çıkılıyor...")
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
        print(f"👤 {idx}. hesap aktif: {me.first_name} (@{me.username})")
    except Exception as e:
        print(f"❌ {idx}. hesap bilgisi alınamadı: {e}")
        return

    @client.on(events.NewMessage(chats=target_channel))
    async def handler(event):
        print(f"📩 {me.username} yeni mesaj gördü: {event.raw_text[:50]}...")

        try:
            # 3 tur reaction bırak (her turda farklı emoji seç)
            for round_num in range(1, 4):
                emoji = random.choice(emojis)
                await client(SendReactionRequest(
                    peer=event.chat_id,
                    msg_id=event.id,
                    reaction=[ReactionEmoji(emoticon=emoji)]
                ))
                print(f"💬 {me.username} Round {round_num} reaction bıraktı: {emoji}")
                await asyncio.sleep(2)
        except Exception as e:
            print(f"⚠️ Reaction hatası ({me.username}): {e}")

    return client


async def general_chat_loop(clients, accounts):
    print("🔄 Genel chat loop başlatıldı (round-robin)")
    while True:
        for idx, client in enumerate(clients):
            if not client:
                continue
            try:
                me = await client.get_me()
            except Exception as e:
                print(f"⚠️ {idx+1}. hesap get_me hatası: {e}")
                continue

            msg = random.choice(general_msgs) if general_msgs else "🔥 Bullish vibes!"
            for g in groups:
                try:
                    sent = await client.send_message(g, msg)
                    print(f"💬 {me.username} ({idx+1}) genel mesaj attı: {msg}")
                    await asyncio.sleep(2)

                    if stickers:
                        sticker = random.choice(stickers)
                        await client.send_file(g, sticker, reply_to=sent.id)
                        print(f"🎨 {me.username} ({idx+1}) sticker attı")
                        await asyncio.sleep(2)

                except Exception as e:
                    print(f"⚠️ Genel sohbet hatası ({me.username}): {e}")

        print("⏳ Tüm kullanıcılar mesaj+sticker attı, bekleniyor...")
        await asyncio.sleep(random.randint(200, 300))


async def conversation_loop(clients, accounts):
    print("🔄 Conversation loop başlatıldı")
    while True:
        block = random.choice(conversations)
        print(f"🗨️ Yeni conversation başladı...")
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
                    print(f"⚠️ {sender} için client yok, atlanıyor...")
                    continue
                me = await sender_client.get_me()
            except (ValueError, IndexError) as e:
                print(f"⚠️ {sender} için index hatası: {e}")
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
                    print(f"⚠️ Conversation hatası ({me.username}): {e}")
            await asyncio.sleep(random.randint(20, 40))
        await asyncio.sleep(random.randint(100, 200))


async def main():
    clients = []
    for idx, acc in enumerate(accounts, start=1):
        print(f"🚀 {idx}. hesap başlatılıyor... API_ID={acc['API_ID']}")
        try:
            client = TelegramClient(
                StringSession(acc["STRING_SESSION"]),
                acc["API_ID"],
                acc["API_HASH"]
            )
            await client.start()
            clients.append(client)
            print(f"✅ {idx}. hesap başarıyla giriş yaptı")
        except AuthKeyDuplicatedError:
            print(f"❌ {idx}. hesap geçersiz (AuthKeyDuplicatedError), atlanıyor...")
            clients.append(None)
        except Exception as e:
            print(f"❌ {idx}. hesap başlatılamadı: {e}")
            clients.append(None)

    aktif = [c for c in clients if c]
    print(f"✅ {len(aktif)} client aktif edildi, {len(clients)-len(aktif)} hata verdi")

    for idx, client in enumerate(clients, start=1):
        if client:
            print(f"▶️ client_worker başlatılıyor: {idx}")
            asyncio.create_task(client_worker(idx, accounts[idx-1], client, clients))
            await asyncio.sleep(2)

    if not aktif:
        print("❌ Hiç client başlatılamadı, çıkılıyor...")
        return

    asyncio.create_task(general_chat_loop(aktif, accounts))
    asyncio.create_task(conversation_loop(aktif, accounts))

    try:
        await asyncio.gather(*(c.run_until_disconnected() for c in aktif))
    finally:
        for client in aktif:
            await client.disconnect()
        print("🛑 Tüm clientler kapatıldı.")


if __name__ == "__main__":
    print("🔥 Bot başlatılıyor...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Manuel durdurma yapıldı.")
