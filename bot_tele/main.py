from typing import Final
from dotenv import load_dotenv
import os
import requests
from telegram import Update, Bot
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters)
import asyncio
import hashlib

load_dotenv(override=True)

TOKEN: Final = os.getenv("TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")
BASE_URL: Final = os.getenv("BASE_URL")
URL_IMAGE: Final = os.getenv("URL_IMAGE")

# bot = Bot(token=TOKEN)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await update.message.reply_text(
        f"Hello! Saya adalah bot tanaman otomatis.\n"
        f"Chat ID kamu: {chat_id}\n"
        "Gunakan perintah /help untuk menampilkan bantuan."
        
    )


async def add_pot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and len(context.args) > 0:
        pot_id = int(context.args[0])
        chat_id = update.message.chat_id

        try:
            api_url = f"{BASE_URL}/insert/user"
            payload = {"pot_id": pot_id, "chat_id": chat_id}
            response = requests.post(api_url, json=payload)

            if response.status_code == 201:
                await update.message.reply_text(
                    f"✅ Pot ID: {pot_id} berhasil ditambahkan ke akun kamu."
                )
            elif response.status_code == 500:
                await update.message.reply_text(
                    "❌ Gagal menambahkan pot. Pot ID sudah terdaftar."
                )
            else:
                await update.message.reply_text(
                    f"❌ Gagal menambahkan pot. Status code: {response.status_code}"
                )

        except requests.RequestException as e:
            await update.message.reply_text(f"❌ Error connecting to the server: {e}")
    else:
        await update.message.reply_text(
            "❌ Silakan masukkan pot ID yang ingin ditambahkan.\n"
            "Contoh: /add_pot 12345\n"
        )

async def remove_pot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and len(context.args) > 0:
        try:
            pot_id = int(context.args[0])
            chat_id = update.message.chat_id
            
            pots = await get_user_pots(chat_id)
            
            if pot_id not in pots:
                await update.message.reply_text(
                    f"❌ Pot ID {pot_id} tidak ditemukan di akun kamu."
                )
                return
            
            api_url = f"{BASE_URL}/destroy/pot"
            payload = {"pot_id": pot_id, "chat_id": chat_id}
            response = requests.post(api_url, json=payload)

            if response.status_code == 201:
                await update.message.reply_text(
                    f"✅ Pot ID: {pot_id} berhasil dihapus dari akun kamu."
                )
            else:
                await update.message.reply_text(
                    f"❌ Gagal menghapus pot. Pot tidak ditemukan atau terjadi kesalahan."
                )
                print(f"Error in remove_pot: {response.status_code}")
                
        except ValueError:
            await update.message.reply_text(
                "❌ Silakan masukkan pot ID yang valid.\n"
                "Contoh: /remove_pot 12345\n"
            )
        except requests.RequestException as e:
            await update.message.reply_text(f"❌ Error connecting to the server: {e}")
    else:
        await update.message.reply_text(
            "❌ Silakan masukkan pot ID yang ingin dihapus.\n"
            "Contoh: /remove_pot 12345\n"
        )
        

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Saya bisa menjalankan perintah berikut:\n"
        "/start - Mulai\n"
        "/sensor - Melihat sensor data\n"
        "/add_pot - Menambahkan pot\n"
        "/my_pots - Melihat pot yang terdaftar\n"
        "/help - Menampilkan bantuan\n"
        "/remove_pot - Menghapus pot\n"
    )


async def get_user_pots(chat_id: int):
    """Mengambil pot pengguna"""
    try:
        response = requests.get(f"{BASE_URL}/find/pot/{chat_id}")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.RequestException:
        return []


async def my_pots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """"Menampilkan pot pengguna"""
    chat_id = update.message.chat_id
    pots = await get_user_pots(chat_id)

    if pots:
        message = "🪴 Pot yang terdaftar:\n\n"
        for pot_id in pots:  # pots is a list of integers
            message += f"🪴 Pot ID: {pot_id}\n"
        await update.message.reply_text(message)
    else:
        await update.message.reply_text(
            "❌ Kamu tidak memiliki pot terdaftar.\n"
            "Gunakan /add_pot [pot_id] untuk menambahkan pot."
        )


async def sensor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    pots = await get_user_pots(chat_id)

    if not pots:
        await update.message.reply_text(
            "❌ Kamu tidak memiliki pot terdaftar.\n"
            "Gunakan /add_pot [pot_id] untuk menambahkan pot."
        )
        return

    if context.args and len(context.args) > 0:
        try:
            specified_pot_id = int(context.args[0])
            if specified_pot_id in pots:
                await send_sensor_data_for_pot(chat_id, specified_pot_id, context.bot)
            else:
                await update.message.reply_text(
                    f"❌ Pot ID {specified_pot_id} tidak ditemukan di akun kamu."
                )
        except ValueError:
            await update.message.reply_text(
                "❌ Silakan masukkan pot ID yang valid.\n"
                "Contoh: /sensor 12345\n"
            )
    else:
        for pot_id in pots:
            await send_sensor_data_for_pot(chat_id, pot_id, context.bot)


async def send_sensor_data_for_pot(chat_id: int, pot_id: int, bot):
    try:
        response = requests.get(f"{BASE_URL}/find/data/{pot_id}")
        data = response.json()

        if data and len(data) > 0:
            sensor_data = data[-1]
            soil_value = sensor_data.get('soil', 'N/A')
            ph_value = sensor_data.get('ph', 'N/A')
            
            soil_status = "N/A"
            if soil_value != 'N/A':
                try:
                    soil_float = float(soil_value)
                    if soil_float < 20:
                        soil_status = "TERLALU KERING ⚠️"
                    elif soil_float < 40:
                        soil_status = "Kering"
                    elif soil_float < 70:
                        soil_status = "Ideal"
                    else:
                        soil_status = "Basah"
                except (ValueError, TypeError):
                    soil_status = "N/A"
            
            ph_status = "N/A"
            if ph_value != 'N/A':
                try:
                    ph_float = float(ph_value)
                    if ph_float < 5:
                        ph_status = "TERLALU ASAM ⚠️"
                    elif ph_float < 6.5:
                        ph_status = "Asam"
                    elif ph_float <= 7.5:
                        ph_status = "Netral (Ideal)"
                    elif ph_float <= 8:
                        ph_status = "Basa"
                    else:
                        ph_status = "TERLALU BASA ⚠️"
                except (ValueError, TypeError):
                    ph_status = "N/A"

            message = (
                f"🌱 Sensor untuk Pot #{pot_id}:\n"
                f"Soil Moisture: {soil_value} - {soil_status}\n"
                f"pH: {ph_value} - {ph_status}\n"
            )

            await bot.send_message(chat_id=chat_id, text=message)
        else:
            await bot.send_message(
                chat_id=chat_id, text=f"Tidak ada data sensor untuk Pot #{pot_id}"
            )
    except requests.RequestException as e:
        await bot.send_message(
            chat_id=chat_id, text=f"Error connecting to the server for Pot #{pot_id}: {e}"
        )
    except Exception as e:
        await bot.send_message(
            chat_id=chat_id, text=f"Data untuk Pot #{pot_id} tidak tersedia."
        )
        print(f"Error in send_sensor_data_for_pot: {e}")


async def check_new_images(app):
    """Check for new images every 10 minutes and send them to users"""
    latest_image_hashes = {}
    
    while True:
        try:
            print("Image check starting...")
            all_users_response = requests.get(f"{BASE_URL}/find/users")
            if all_users_response.status_code == 200:
                response_data = all_users_response.json()

                if "chat_ids" in response_data:
                    chat_ids = response_data["chat_ids"]
                    print(f"Found {len(chat_ids)} users for image notifications")

                    # Process each chat_id
                    for chat_id in chat_ids:
                        pots = await get_user_pots(chat_id)
                        print(f"User {chat_id} has {len(pots)} pots to check for images")

                        for pot_id in pots:
                            try:
                                image_response = requests.get(f"{BASE_URL}/get/image/{pot_id}")
                                
                                if image_response.status_code == 200:
                                    content_type = image_response.headers.get('Content-Type', '')
                                    
                                    if 'image' in content_type.lower():
                                        print(f"Received direct image for pot {pot_id} (Content-Type: {content_type})")
                                        
                                        content_hash = hashlib.md5(image_response.content).hexdigest()
                                        
                                        pot_key = f"{chat_id}_{pot_id}"
                                        
                                        should_send = False
                                        if pot_key not in latest_image_hashes:
                                            should_send = True
                                            print(f"First image for {pot_key}, sending (hash: {content_hash[:8]}...)")
                                        elif latest_image_hashes[pot_key] != content_hash:
                                            should_send = True
                                            print(f"New image content for {pot_key}. Old hash: {latest_image_hashes[pot_key][:8]}..., New hash: {content_hash[:8]}...")
                                        else:
                                            print(f"Same image content for {pot_key}, skipping (hash: {content_hash[:8]}...)")
                                            
                                        if should_send:
                                            latest_image_hashes[pot_key] = content_hash
                                            
                                            try:
                                                await app.bot.send_photo(
                                                    chat_id=chat_id,
                                                    photo=image_response.content,
                                                    caption=f"🌱 Gambar baru untuk Pot #{pot_id}"
                                                )
                                                print(f"Direct image sent successfully to {chat_id} for pot {pot_id}")
                                            except Exception as e:
                                                print(f"Failed to send direct image: {e}")
                                    else:
                                        print(f"Unsupported content type for pot {pot_id}: {content_type}")
                                else:
                                    print(f"Failed to get image for pot {pot_id}: {image_response.status_code}")
                            except Exception as e:
                                print(f"Error checking images for pot {pot_id}: {e}")
                else:
                    print("Response does not contain 'chat_ids' field")
            else:
                print(f"Failed to fetch users for image check: status code {all_users_response.status_code}")
        except Exception as e:
            print(f"Error in image check: {e}")

        print("Image check complete, sleeping for 10 minutes...")
        await asyncio.sleep(600)


async def auto_notify(app):
    SOIL_MIN_THRESHOLD = 20  # Minimum acceptable soil moisture (%)
    PH_MIN_THRESHOLD = 5  # Minimum acceptable pH level
    PH_MAX_THRESHOLD = 8  # Maximum acceptable pH level

    while True:
        try:
            print("Auto notify check starting...")
            all_users_response = requests.get(f"{BASE_URL}/find/users")
            if all_users_response.status_code == 200:
                response_data = all_users_response.json()

                if "chat_ids" in response_data:
                    chat_ids = response_data["chat_ids"]
                    print(f"Found {len(chat_ids)} users")

                    # Process each chat_id
                    for chat_id in chat_ids:
                        pots = await get_user_pots(chat_id)
                        print(f"User {chat_id} has {len(pots)} pots: {pots}")

                        for pot_id in pots:
                            # Check sensor data against thresholds
                            try:
                                response = requests.get(
                                    f"{BASE_URL}/find/data/{pot_id}"
                                )
                                if response.status_code == 200:
                                    data = response.json()

                                    if data and len(data) > 0:
                                        sensor_data = data[-1]  # Get latest reading
                                        soil_value = sensor_data.get("soil")
                                        ph_value = sensor_data.get("ph")

                                        print(
                                            f"Pot {pot_id} - soil: {soil_value}, pH: {ph_value}"
                                        )

                                        # Check if values are outside thresholds
                                        alerts = []

                                        if soil_value is not None:
                                            try:
                                                soil_value = float(soil_value)
                                                print(
                                                    f"Checking soil: {soil_value} < {SOIL_MIN_THRESHOLD}"
                                                )
                                                if soil_value < SOIL_MIN_THRESHOLD:
                                                    alerts.append(
                                                        f"⚠️ Low soil moisture: {soil_value}% | Tanah terlalu kering (di bawah minimum {SOIL_MIN_THRESHOLD}%)"
                                                    )
                                                    print(
                                                        f"Added soil alert for pot {pot_id}"
                                                    )
                                            except (ValueError, TypeError) as e:
                                                print(
                                                    f"Error converting soil value: {e}"
                                                )

                                        if ph_value is not None:
                                            try:
                                                ph_value = float(ph_value)
                                                print(
                                                    f"Checking pH: {ph_value} < {PH_MIN_THRESHOLD} or > {PH_MAX_THRESHOLD}"
                                                )
                                                if ph_value < PH_MIN_THRESHOLD:
                                                    alerts.append(f"⚠️ Low pH level: {ph_value} | Tanah terlalu asam (di bawah {PH_MIN_THRESHOLD})")
                                                    print(f"Added low pH alert for pot {pot_id}")
                                                elif ph_value > PH_MAX_THRESHOLD:
                                                    alerts.append(f"⚠️ High pH level: {ph_value} | Tanah terlalu basah (di atas {PH_MAX_THRESHOLD})")
                                                    print(f"Added high pH alert for pot {pot_id}")
                                            except (ValueError, TypeError) as e:
                                                print(f"Error converting pH value: {e}")

                                        # If any alerts, send notification
                                        if alerts:
                                            alert_message = (f"🚨 ALERT UNTUK POT #{pot_id}:\n\n"+ "\n".join(alerts))
                                            alert_message += (
                                                "\n\nSegera Cek Air atau Pupuk Tanamanmu!"
                                            )
                                            print(
                                                f"Sending alert to {chat_id}: {alert_message}"
                                            )
                                            try:
                                                await app.bot.send_message(
                                                    chat_id=chat_id, text=alert_message
                                                )
                                                print(
                                                    f"Alert sent successfully to {chat_id}"
                                                )
                                            except Exception as e:
                                                print(f"Failed to send alert: {e}")
                                    else:
                                        print(f"No sensor data for pot {pot_id}")
                            except Exception as e:
                                print(
                                    f"Error checking thresholds for pot {pot_id}: {e}"
                                )
                else:
                    print("Response does not contain 'chat_ids' field")
                    print(f"Response content: {response_data}")
            else:
                print(
                    f"Failed to fetch users: status code {all_users_response.status_code}"
                )
        except Exception as e:
            print(f"Error in auto notify: {e}")

        print("Auto notify check complete, sleeping for 1 hour...")
        await asyncio.sleep(3600)  # 1 hour


def handle_response(text: str) -> str:
    processed: str = text.lower()
    if "hi" in processed or "hello" in processed:
        return "Hi! Ada yang bisa saya bantu?"
    if "help" in processed:
        return "Boleh! Saya bisa membantu kamu dengan perintah /help:\n"
    if "Ngulik Boys?" in processed:
        return "Jaya Jaya Jaya"

    return "Maaf, saya tidak mengerti apa yang kamu katakan."


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f"User ({update.message.chat.id}) in {message_type} said: {text}")

    if message_type == "group":
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, "").strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)

    print(f"Bot response: {response}")
    await update.message.reply_text(response)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")


async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("sensor", sensor))
    app.add_handler(CommandHandler("add_pot", add_pot))
    app.add_handler(CommandHandler("my_pots", my_pots))
    app.add_handler(CommandHandler("remove_pot", remove_pot))

    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_error_handler(error)

    print("Bot is running...")
    async with app:
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        try:
            auto_notify_task = asyncio.create_task(auto_notify(app))
            check_image_task = asyncio.create_task(check_new_images(app))
            
            await asyncio.gather(auto_notify_task, check_image_task)
        except asyncio.CancelledError:
            pass
        finally:
            await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
