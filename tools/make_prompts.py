"""Write each character's art brief for Codex: one shared frame, so the nine pictures are one series,
and a few lines of her own for who she is and where she sits.

python make_prompts.py <briefs.json> <out folder> [id ...]
"""
import json
import os
import sys

FRAME = """Use your built-in image generation tool (not code, not a drawing script) to create ONE illustration. Generate it in landscape orientation (16:9) at the largest size the tool offers. Save the result as scene.png in the current directory, then stop. Do not write or run any other code and do not change any other file.

Two images are attached.
1. The FIRST image is a character sheet: one girl seen from the front, from behind and from three-quarters behind. She is the girl in this picture: draw her design faithfully (hair, ears, horns, tail or wings if she has them, clothes, colours).
2. The SECOND image is a finished picture from the same series. Match its painting style, its darkness, its depth, its lighting and its composition closely, so the two belong side by side. Do NOT copy its setting or its girl: the new picture has its own place and its own girl.

ART BRIEF

Subject: {subject}

Viewpoint: from behind and a little above her. She is in the RIGHT third of the picture, her back to the viewer; we see her back, her hair, and at most a hint of cheek. She takes up about a third of the picture's height. {pose}

The girl, as in the character sheet: {girl} Her hair falls loose down her back where the design allows, and reads clearly apart from her clothes and from what is behind it.

Beside her: {beside}

The place: {place} Strong depth, layer upon layer receding, with thin haze between near and far, and tiny lights far off to give scale.

Mood: secluded, deep, hushed, dark, a little mysterious. It is late at night and she is alone. Low-key lighting; most of the picture is in shadow.

Colour: deep blue-black, slate and desaturated teal in the shadows; {colour}

Composition rule (the picture sits behind text in an app): the LEFT 55 percent of the image, and above all its upper left, must stay calm and dark: distant forms fading into dim haze, with no bright lights and no hard contrast there. Keep the brightest things (her lamp, the main light, the girl) on the right.

Style: the background art of a high-budget anime film crossed with painterly fantasy concept art: rich detail, soft volumetric light, fine brushwork, cinematic. Not photorealistic, not plastic-looking 3D. No text, no letters, no numbers, no logos, no watermark, no signature, no border, no interface elements.
"""

briefs = json.load(open(sys.argv[1], encoding='utf-8'))
out = sys.argv[2]
for cid in sys.argv[3:] or list(briefs):
    b = briefs[cid]
    os.makedirs(os.path.join(out, cid), exist_ok=True)
    open(os.path.join(out, cid, 'prompt.txt'), 'w', encoding='utf-8', newline='\n').write(FRAME.format(**b))
    print(cid, 'brief written')
