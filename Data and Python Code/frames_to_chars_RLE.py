from PIL import Image
import os
from itertools import groupby
from alive_progress import alive_bar, alive_it    # Let's make it pretty

charset = list()
charset_dict = {}  # {character : index in charset} (speed up! 240+ frames/sec)
frames = list()

# This version of the script is provided as-is. While it does produce a valid RLE, it ends up being too big for the MSP.
# Fixing that is left as an exercise for the reader :^)

# Note to self: getpixel() pixels are 0 if black, 255 if white for grayscale or 1-bit BMPs

##########################
# --- PROCESS FRAMES --- #
##########################

# path = "C:/Users/Austin/Documents/Bad Apple/bad_apple_64x48_bmp/"
path = "D:/Austin/Documents/School Stuff/ECEN 260/bad_apple_64x48_bmp/"
files = os.listdir(path)[::3]   # Slice to get every third frame

# Make this a function so I can use return to break the whole loop nest
def process_files():
    # For each frame (with a cool progress bar):
    for file in alive_it(files, bar="filling", spinner="twirls", title="Processing frames...", finalize=lambda bar: bar.title("Frames processed!")):
        with Image.open(path + file) as im:    
            # Resize it to 32x24
            im = im.resize((32, 24))
            im = im.resize((64, 48))
            #im.show()
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

                # Just get a 256 char set for now
                if len(charset) >= 256:
                    return

                # Add new chars to charset and its dict
                if len(charset) < 256 and char not in charset_dict:
                    # TODO use better algorithm
                    charset.append(char)
                    charset_dict[char] = len(charset) - 1
                
                # TODO append similar_char
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


##########################
# --- RLE THE FRAMES --- #
##########################

# Run-length encode the frames to save space(?)
# Data byte, then length/repetition byte
def rle_frames(frames):
    for i, frame in alive_it(enumerate(frames), bar="filling", spinner="twirls", title="Encoding frames...", finalize=lambda bar: bar.title("Frames encoded!")):
        # RLE the frame (creates a list of lists)
        rle_list = [[key, len(list(group))] for key, group in groupby(frame)]
        # Flatten the list list to a list of ints
        flat_list = sum(rle_list, [])
        # print(frame)
        # print(rle_list)
        # print(flat_list)
        # Replace frame with RLEd frame
        frames[i] = flat_list


    return frames

frames = rle_frames(frames)
max_length = len(max(frames, key=lambda i: len(i)))

print(f"Max length of a frame: {max_length}")

#######################
# --- WRITE FILES --- #
#######################

# destination = "C:/Users/Austin/workspace_v12/final_project/"
destination = path + "processed/"

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
    fr.write("#ifndef FRAMES_H_\n#define FRAMES_H_\n\n")
    c_str = "const unsigned char *frames[] = " + str(frames).replace("(", "{").replace("),", "},\n").replace(")", "}").replace("],", "},\n").replace("]", "}").replace("[", "(unsigned char[]){").replace(", ", ",") + ";"
    fr.write(c_str)
    fr.write("\n\n#endif\n")
print(f"Frame sequence saved to {destination}frames.h")
