# app.py
import os
import io
import base64
import zipfile

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_file,
    flash,
)

from PIL import Image
from pillow_heif import register_heif_opener

from modules.background_ops import (
    remove_background,
    replace_background_color,
    replace_background_image,
    blur_background,
    uniform_resize,
)

register_heif_opener()

app = Flask(__name__)
app.secret_key = "super-secret-key"   # change this in production!

# Paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SAMPLES_DIR = os.path.join(BASE_DIR, "static", "samples")


# ---------- Helper functions ----------

def pil_to_base64(img, format="PNG"):
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def load_any_image(file_storage):
    """Load any uploaded image into RGB PIL Image."""
    return Image.open(file_storage.stream).convert("RGB")


# ---------- Routes ----------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/background-removal", methods=["GET", "POST"])
def background_removal():
    input_b64 = None
    output_b64 = None

    if request.method == "POST":
        file = request.files.get("image")
        if not file or file.filename == "":
            flash("Please upload an image.", "error")
            return redirect(request.url)

        try:
            img = load_any_image(file)
            out, _ = remove_background(img)

            input_b64 = pil_to_base64(img)
            output_b64 = pil_to_base64(out)

        except Exception as e:
            flash(f"Error processing image: {e}", "error")

    return render_template(
        "background_removal.html",
        input_b64=input_b64,
        output_b64=output_b64,
    )


@app.route("/background-replace", methods=["GET", "POST"])
def background_replace():
    mode = "color"        # default
    input_b64 = None
    output_b64 = None
    selected_color = "#ffffff"

    # GET → show empty page
    if request.method == "GET":
        return render_template(
            "background_replace.html",
            mode=mode,
            input_b64=None,
            output_b64=None,
            selected_color=selected_color
        )

    # POST → always read mode first
    mode = request.form.get("mode", "color")

    # Always load main image, if provided
    file = request.files.get("image")
    if file and file.filename != "":
        img = Image.open(file.stream).convert("RGB")
        input_b64 = pil_to_base64(img)
    else:
        flash("Please upload a main image.", "error")
        return render_template(
            "background_replace.html",
            mode=mode,
            input_b64=None,
            output_b64=None,
            selected_color=selected_color
        )

    # Now process depending on mode
    try:
        if mode == "color":
            selected_color = request.form.get("color", "#ffffff")
            out = replace_background_color(img, selected_color)

        elif mode == "image":
            bg_file = request.files.get("bg_image")
            if not bg_file or bg_file.filename == "":
                flash("Please upload a background image.", "error")
                return render_template(
                    "background_replace.html",
                    mode=mode,
                    input_b64=input_b64,
                    output_b64=None,
                    selected_color=selected_color
                )
            bg_img = Image.open(bg_file.stream).convert("RGB")
            out = replace_background_image(img, bg_img)

        # Generate output preview
        output_b64 = pil_to_base64(out)

    except Exception as e:
        flash(f"Error: {e}", "error")

    return render_template(
        "background_replace.html",
        mode=mode,
        input_b64=input_b64,
        output_b64=output_b64,
        selected_color=selected_color
    )

@app.route("/blur-background", methods=["GET", "POST"])
def blur_background_page():
    input_b64 = None
    output_b64 = None
    blur_px = int(request.form.get("blur_px", "25"))

    if request.method == "POST":
        file = request.files.get("image")
        if not file or file.filename == "":
            flash("Please upload an image.", "error")
            return redirect(request.url)

        try:
            img = load_any_image(file)
            out = blur_background(img, blur_px)

            input_b64 = pil_to_base64(img)
            output_b64 = pil_to_base64(out)

        except Exception as e:
            flash(f"Error processing image: {e}", "error")

    return render_template(
        "blur_background.html",
        input_b64=input_b64,
        output_b64=output_b64,
        blur_px=blur_px,
    )


# IMPORTANT: global variable to store zip temporarily
BATCH_ZIP_BUFFER = None


@app.route("/batch-processing", methods=["GET", "POST"])
def batch_processing():
    global BATCH_ZIP_BUFFER

    if request.method == "POST":
        if "images" not in request.files:
            return render_template("batch_processing.html", outputs=None)

        files = request.files.getlist("images")

        outputs = []
        zip_buffer = io.BytesIO()
        zip_file = zipfile.ZipFile(zip_buffer, "w")

        for f in files:
            try:
                # Load image
                img = Image.open(f.stream).convert("RGB")

                # Remove background
                result, _ = remove_background(img)

                # Convert to base64 for browser
                buf = io.BytesIO()
                result.save(buf, format="PNG")
                b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")

                outputs.append({
                    "name": f.filename,
                    "b64": b64_str
                })

                # Add to zip
                zip_file.writestr(
                    f.filename.replace(".", "_processed."), 
                    buf.getvalue()
                )

            except Exception as e:
                print("Error processing:", f.filename, e)
                continue

        zip_file.close()
        zip_buffer.seek(0)
        BATCH_ZIP_BUFFER = zip_buffer  # store for download

        return render_template("batch_processing.html", outputs=outputs)

    return render_template("batch_processing.html", outputs=None)



@app.route("/download-zip")
def download_zip():
    global BATCH_ZIP_BUFFER
    if BATCH_ZIP_BUFFER is None:
        return redirect(url_for("batch_processing"))

    BATCH_ZIP_BUFFER.seek(0)
    return send_file(
        BATCH_ZIP_BUFFER,
        mimetype="application/zip",
        as_attachment=True,
        download_name="batch_processed.zip"
    )


@app.route("/sample-gallery")
def sample_gallery():
    import os

    sample_dir = os.path.join("static", "samples")
    if not os.path.exists(sample_dir):
        files = []
    else:
        files = [
            f for f in os.listdir(sample_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
        ]

    return render_template("sample_gallery.html", files=files)


@app.route("/about")
def about():
    return render_template("about.html")


# ---------- Run ----------

if __name__ == "__main__":
    # debug for development
    app.run(host="0.0.0.0", port=5000, debug=True)
