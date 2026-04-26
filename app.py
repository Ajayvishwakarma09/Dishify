from flask import Flask, render_template, request, jsonify
import os
import json
import re

from models.vision_model import FoodVisionModel
from models.youtubeapi import YouTubeAPI

app = Flask(__name__)

# -----------------------------
# CONFIG
# -----------------------------
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------
# LOAD JSON (FIXED PATH)
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, "recipes.json")

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

recipes = data["recipes"]

# -----------------------------
# MODELS
# -----------------------------
vision_model = FoodVisionModel()

# ❌ REMOVE HARDCODED KEY
# YOUTUBE_KEY = "AIzaSy..."

# ✅ USE ENV VARIABLE
YOUTUBE_KEY = os.getenv("YOUTUBE_API_KEY")

youtube_api = YouTubeAPI(YOUTUBE_KEY)

# -----------------------------
# FUNCTIONS
# -----------------------------
def find_recipe(dish_name):
    if not dish_name:
        return None

    dish_name = dish_name.lower()

    for recipe in recipes:
        if dish_name in recipe["name"].lower():
            return recipe

    return None


def scale_ingredients(recipe, people):
    try:
        base_servings = int(str(recipe["servings"]).split()[0])
    except:
        base_servings = 1

    factor = people / base_servings
    scaled = []

    for ing in recipe["ingredients"]:
        try:
            amount = float(ing["amount"]) * factor
        except:
            amount = ing["amount"]

        scaled.append({
            "name": ing["name"],
            "amount": round(amount, 2) if isinstance(amount, float) else amount,
            "unit": ing["unit"]
        })

    return scaled


# -----------------------------
# MAIN ROUTE
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        people = int(request.form.get("people", 1))

        dish_name = request.form.get("dish_name")
        image = request.files.get("image")

        image_path = None
        dish = None

        # CASE 1 → Manual search
        if dish_name and dish_name.strip() != "":
            dish = dish_name.strip()

        # CASE 2 → Image upload
        elif image and image.filename != "":

            filename = image.filename.lower()
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image.save(image_path)

            name_without_ext = os.path.splitext(filename)[0]

            clean_name = re.sub(r'[^a-zA-Z ]', ' ', name_without_ext)
            clean_name = clean_name.strip()

            recipe = find_recipe(clean_name)

            if recipe:
                dish = recipe["name"]
            else:
                dish = vision_model.predict_dish(image_path)

        # fallback
        if not dish:
            dish = "food"

        recipe = find_recipe(dish)

        if recipe:
            ingredients = scale_ingredients(recipe, people)
            steps = recipe.get("steps", [])

            description = recipe.get("description", "")
            prepTime = recipe.get("prepTime", "")
            cookTime = recipe.get("cookTime", "")
            totalTime = recipe.get("totalTime", "")
            cuisine = recipe.get("cuisine", "")
            category = recipe.get("category", "")

        else:
            ingredients = []
            steps = []
            description = "Recipe not found"
            prepTime = ""
            cookTime = ""
            totalTime = ""
            cuisine = ""
            category = ""

        videos = youtube_api.get_videos(dish)

        return render_template(
            "result.html",
            dish=dish,
            ingredients=ingredients,
            steps=steps,
            description=description,
            prepTime=prepTime,
            cookTime=cookTime,
            totalTime=totalTime,
            cuisine=cuisine,
            category=category,
            videos=videos,
            image_path=image_path
        )

    return render_template("index.html")


# -----------------------------
# AUTO SUGGEST
# -----------------------------
@app.route("/suggest")
def suggest():

    query = request.args.get("q", "").lower()
    suggestions = []

    for recipe in recipes:
        name = recipe["name"]

        if query in name.lower():
            suggestions.append(name)

        if len(suggestions) >= 5:
            break

    return jsonify({"suggestions": suggestions})


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)