from PIL import Image
import os, glob
from alive_progress import alive_bar, alive_it    # Let's make it pretty

charset = list()
charset_dict = {}  # {character : index in charset} (speed up! 240+ frames/sec)
frames = list()

# Note to self: getpixel() pixels are 0 if black, 255 if white for grayscale or 1-bit BMPs

##########################
# --- CONFIG OPTIONS --- #
##########################

# Path of .bmp frames - extract the .7z
path = "C:/Users/Austin/Documents/Bad Apple/bad_apple_64x48_bmp/"
# Using zipfile may not have been the worst idea...

# Path to write the data files (must exist)
destination = path + "processed/"

# divide source framerate (30 in this case) by:
fps_divisor = 3

# For now this is hardcoded to work with 64x48 frames and half their resolution first.


##########################
# --- PROCESS FRAMES --- #
##########################

# Get every .bmp in the path
files = glob.glob('*.bmp', root_dir=path)[::fps_divisor]   # Slice to get every (whatever)th frame

# Make this a function so I can use return to break the whole loop nest
def process_files():
    # For each frame (with a cool progress bar):
    for file in alive_it(files, bar="filling", spinner="twirls", title="Processing frames...", finalize=lambda bar: bar.title("Frames processed!")):
    # If you don't want to install alive_progress, use this instead
    # for file in files:
        with Image.open(path + file) as im:    
            # Resize it to 32x24 and back
            im = im.resize((32, 24))
            im = im.resize((64, 48))
            x_offset, y_offset = 0, 0
            this_frame = list()
            # Go until all chars are read
            while x_offset < 64 and y_offset < 48:
                # Per character:
                char = tuple()  # because you can't have a set/dict of lists :(

                # Read character to char
                for x in range(4):
                    # Per byte column:
                    byte = 0
                    for y in range(8):
                        px = (im.getpixel((x+x_offset, y+y_offset)) // 255) ^ 1  # int divide by 255, then XOR with 1 to get 1 for black/0 for white
                        byte |= px << y  # add to byte (shift to appropriate bit)

                    char += (byte,)  # tuple append

                # Ensure a 256 char set
                # Hey, guess how many 2x4 characters there are?
                if len(charset) >= 256:
                    return

                # Add new chars to charset and its dict
                if char not in charset_dict:
                    charset.append(char)
                    charset_dict[char] = len(charset) - 1
                
                this_frame.append(charset_dict[char])  # add this char('s index) to this frame

                # Next character
                x_offset += 4

                # Wrap around if it's time to
                if x_offset == 64:
                    x_offset = 0
                    y_offset += 8

            # Done with this frame
            if len(this_frame) == 96: frames.append(this_frame)

process_files()
print("Made a", len(charset), "character set")


#######################
# --- WRITE FILES --- #
#######################

# These will come out with correct C syntax
# Write charset
with open(destination + "charset.h", "w") as cs:
    cs.write("#ifndef CHARSET_H_\n#define CHARSET_H_\n\n")
    c_str = "const unsigned char charset[][4] = " + str(charset).replace("[", "{").replace("(", "{").replace("],", "},\n").replace("),", "},\n").replace(")", "}").replace("]", "}").replace(", ", ",") + ";"
    cs.write(c_str)
    cs.write("\n\n#endif\n")
print(f"Charset saved to {destination}charset.h")

# Write frame sequence
with open(destination + "frames.h", "w") as fr:
    fr.write(f"#ifndef FRAMES_H_\n#define FRAMES_H_\n\n#define NUMFRAMES {len(frames)}\n\n")
    c_str = "const unsigned char frames[][96] = " + str(frames).replace("[", "{").replace("(", "{").replace("],", "},\n").replace("),", "},\n").replace(")", "}").replace("]", "}").replace(", ", ",") + ";"
    fr.write(c_str)
    fr.write("\n\n#endif\n")
print(f"Frame sequence saved to {destination}frames.h")
