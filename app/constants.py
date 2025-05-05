import os

from discord import Color

_color = os.environ.get("PRIMARY_COLOR", "#7c4f9c")
PRIMARY_COLOR = Color(int(_color.strip("#"), 16))

NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
