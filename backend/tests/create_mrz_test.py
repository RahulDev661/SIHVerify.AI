from PIL import Image, ImageDraw, ImageFont


# -----------------------------------------
# CREATE TEST DOCUMENT
# -----------------------------------------

width = 1400
height = 900

image = Image.new(
    "RGB",
    (width, height),
    "white"
)

draw = ImageDraw.Draw(image)


# -----------------------------------------
# FONTS
# -----------------------------------------

try:

    title_font = ImageFont.truetype(
        "arial.ttf",
        42
    )

    text_font = ImageFont.truetype(
        "arial.ttf",
        32
    )

    mrz_font = ImageFont.truetype(
        "cour.ttf",
        40
    )

except:

    title_font = ImageFont.load_default()
    text_font = ImageFont.load_default()
    mrz_font = ImageFont.load_default()


# -----------------------------------------
# NORMAL DOCUMENT DATA
# -----------------------------------------

draw.text(
    (80, 60),
    "VERIDEX DOCUMENT SCREENING",
    fill="black",
    font=title_font
)

draw.text(
    (80, 150),
    "Name: RAHUL DEV BERA",
    fill="black",
    font=text_font
)

draw.text(
    (80, 210),
    "Passport Number: P1234567",
    fill="black",
    font=text_font
)

draw.text(
    (80, 270),
    "Date of Birth: 12/05/2004",
    fill="black",
    font=text_font
)

draw.text(
    (80, 330),
    "Nationality: IND",
    fill="black",
    font=text_font
)

draw.text(
    (80, 390),
    "Expiry: 12/05/2030",
    fill="black",
    font=text_font
)


# -----------------------------------------
# MRZ
# -----------------------------------------

mrz_line1 = "P<INDRAHUL<DEV<BERA<<<<<<<<<<<<<<<<<<<<<<<<<"

mrz_line2 = "P1234567<1IND0405122M3005121<<<<<<<<<<<<<<<<"


draw.text(
    (80, 650),
    mrz_line1,
    fill="black",
    font=mrz_font
)

draw.text(
    (80, 710),
    mrz_line2,
    fill="black",
    font=mrz_font
)


# -----------------------------------------
# SAVE
# -----------------------------------------

image.save(
    "sample_data/test_mrz_document.png"
)

print("MRZ test document created successfully!")

print("Saved as: test_mrz_document.png")

print("Line 1 length:", len(mrz_line1))

print("Line 2 length:", len(mrz_line2))