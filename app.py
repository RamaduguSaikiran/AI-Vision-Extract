import os
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from modules.model_loader import load_model
from modules.background_ops import remove_background, replace_background_color, replace_background_image, blur_background

app = Flask(__name__)
app.secret_key = "super_secret_key"

# LAZY MODEL LOAD
model = None
def get_model():
    global model
    if model is None:
        model = load_model()   # your custom loader
    return model



# INDEX PAGE
@app.route("/")
def index():
    return render_template("index.html", title="AIvision Extract")



# BACKGROUND REMOVAL
@app.route("/background-removal", methods=["GET", "POST"])
def background_removal():
    if request.method == "POST":
        if "image" not in request.files:
            flash("Please upload an image.", "error")
            return redirect(request.url)

        file = request.files["image"]
        if file.filename == "":
            flash("No file selected.", "error")
            return redirect(request.url)

        # save temp upload
        input_path = os.path.join(app.root_path, "static/uploads", file.filename)
        file.save(input_path)

        # run removal
        output_bytes = remove_background(get_model(), input_path)

        # output path
        output_path = os.path.join(app.root_path, "static/outputs", "removed.png")
        with open(output_path, "wb") as f:
            f.write(output_bytes)

        return render_template(
            "background_removal.html",
            input_image=file.filename,
            output_image="removed.png",
        )

    return render_template("background_removal.html")



# BACKGROUND REPLACEMENT
@app.route("/background-replace", methods=["GET", "POST"])
def background_replace_page():
    if request.method == "POST":
        if "main_image" not in request.files:
            flash("Please upload a main image.", "error")
            return redirect(request.url)

        main_file = request.files["main_image"]
        if main_file.filename == "":
            flash("No main image selected.", "error")
            return redirect(request.url)

        main_path = os.path.join(app.root_path, "static/uploads", main_file.filename)
        main_file.save(main_path)

        mode = request.form.get("mode")

        # COLOR MODE
        if mode == "color":
            hex_color = request.form.get("color")
            output_path = os.path.join(app.root_path, "static/outputs", "replaced.png")
            replace_background_color(get_model(), main_path, hex_color, output_path)
            return render_template("background_replace.html",
                                   input_image=main_file.filename,
                                   output_image="replaced.png",
                                   mode="color")

        # IMAGE MODE
        if mode == "image":
            if "bg_image" not in request.files:
                flash("Please upload background image.", "error")
                return redirect(request.url)

            bg_file = request.files["bg_image"]
            bg_path = os.path.join(app.root_path, "static/uploads", bg_file.filename)
            bg_file.save(bg_path)

            output_path = os.path.join(app.root_path, "static/outputs", "replaced.png")
            replace_background_image(get_model(), main_path, bg_path, output_path)

            return render_template("background_replace.html",
                                   input_image=main_file.filename,
                                   output_image="replaced.png",
                                   mode="image")

    return render_template("background_replace.html")



# BLUR PAGE
@app.route("/blur", methods=["GET", "POST"])
def blur_background_page():
    if request.method == "POST":
        if "image" not in request.files:
            flash("Upload an image.", "error")
            return redirect(request.url)

        file = request.files["image"]
        img_path = os.path.join(app.root_path, "static/uploads", file.filename)
        file.save(img_path)

        blur_amount = int(request.form.get("blur", 15))
        output_path = os.path.join(app.root_path, "static/outputs", "blurred.png")

        blur_background(get_model(), img_path, blur_amount, output_path)

        return render_template("blur_background.html",
                               input_image=file.filename,
                               output_image="blurred.png")

    return render_template("blur_background.html")



# BATCH PROCESSING
@app.route("/batch-processing", methods=["GET", "POST"])
def batch_processing():
    if request.method == "POST":
        files = request.files.getlist("images")
        output_folder = os.path.join(app.root_path, "static/batch_outputs")

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        for f in files:
            save_path = os.path.join(output_folder, f.filename)
            f.save(save_path)

            # remove background
            out_path = os.path.join(output_folder, "out_" + f.filename)
            remove_background(get_model(), save_path, save_to=out_path)

        flash("Batch processing completed!", "success")
        return redirect(request.url)

    return render_template("batch_processing.html")



# GALLERY
@app.route("/gallery")
def sample_gallery():
    return render_template("sample_gallery.html")



# ABOUT
@app.route("/about")
def about():
    return render_template("about.html")



# ENTRY POINT FOR RENDER
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=10000)
