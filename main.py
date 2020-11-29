import sys
import fitz
import PySimpleGUI as sg
from sys import exit
import os
import glob
import re
from gtts import gTTS
from pygame import mixer
import time

# sg.theme('GreenTan')

if len(sys.argv) == 1:
    fname = sg.popup_get_file(
        'PDF Browser', 'PDF file to open', file_types=(("PDF Files", "*.pdf"),))
    if fname is None:
        sg.popup_cancel('Cancelling')
        exit(0)
else:
    fname = sys.argv[1]

doc = fitz.open(fname)
page_count = len(doc)

dlist_tab = [None] * page_count

title = "PyMuPDF display of '%s', pages: %i" % (fname, page_count)

curr_dir = os.getcwd()
final_dir = os.path.join(curr_dir, 'software')
if not os.path.exists(final_dir):
    os.makedirs(final_dir)
image_dir = glob.glob(final_dir)
for file_name in os.listdir(final_dir):
    filepath = os.path.join(final_dir, file_name)
    os.chmod(filepath, 0o777)
    os.remove(filepath)

mixer.init()

def get_page(pno, zoom=0):
    """Return a PNG image for a document page number. If zoom is other than 0, one of the 4 page quadrants are zoomed-in instead and the corresponding clip returned.
    """
    dlist = dlist_tab[pno]  # get display list
    if not dlist:  # create if not yet there
        dlist_tab[pno] = doc[pno].getDisplayList()
        dlist = dlist_tab[pno]
    r = dlist.rect  # page rectangle
    mp = r.tl + (r.br - r.tl) * 0.5  # rect middle point
    mt = r.tl + (r.tr - r.tl) * 0.5  # middle of top edge
    ml = r.tl + (r.bl - r.tl) * 0.5  # middle of left edge
    mr = r.tr + (r.br - r.tr) * 0.5  # middle of right egde
    mb = r.bl + (r.br - r.bl) * 0.5  # middle of bottom edge
    mat = fitz.Matrix(2, 2)  # zoom matrix
    if zoom == 1:  # top-left quadrant
        clip = fitz.Rect(r.tl, mp)
    elif zoom == 4:  # bot-right quadrant
        clip = fitz.Rect(mp, r.br)
    elif zoom == 2:  # top-right
        clip = fitz.Rect(mt, mr)
    elif zoom == 3:  # bot-left
        clip = fitz.Rect(ml, mb)
    if zoom == 0:  # total page
        pix = dlist.getPixmap(alpha=False)
    else:
        pix = dlist.getPixmap(alpha=False, matrix=mat, clip=clip)
    output = os.path.join(final_dir, r"image_to_read.png")
    pix.writePNG(output)
    return output


def get_text(pno, start_pt, end_pt):
    page = doc.loadPage(pno)
    text = page.getTextbox(fitz.Rect(start_pt[0], start_pt[1], end_pt[0], end_pt[1]))
    pattern = "\[\d+\]\,*\ *"
    pattern2 = "\[\d+\]\,*\."
    x = re.findall(pattern, text)
    text = re.sub(pattern, "", text)
    text = re.sub(pattern2, ".", text)
    return text


def cleanup():
    for file_name in os.listdir(final_dir):
        filepath = os.path.join(final_dir, file_name)
        os.chmod(filepath, 0o777)
        os.remove(filepath)


cur_page = 0
data = get_page(cur_page) 

goto = sg.InputText(str(cur_page + 1), size=(5, 1))

layout = [
    [
        sg.Button('Prev'),
        sg.Button('Next'),
        sg.Text('Page:'),
        goto,
    ],
    [
        sg.Text("Zoom:"),
        sg.Button('Top-L'),
        sg.Button('Top-R'),
        sg.Button('Bot-L'),
        sg.Button('Bot-R'),
    ],
    [sg.Graph(
    canvas_size=(612, 792),
    graph_bottom_left=(0, 792),
    graph_top_right=(612, 0),
    key="-GRAPH-",
    change_submits=True,
    background_color='lightblue',
    drag_submits=True),
    sg.Frame(layout=[
        [sg.Button("Speak")],
        [sg.Button("Pause")],
        [sg.Button("Unpause")],
        [sg.Button("Stop")]], title='Audio',
             title_color='red',
             relief=sg.RELIEF_SUNKEN,
             tooltip='Use these to set flags')
    ],
    [sg.Text(key='info', size=(60, 1))]
]


my_keys = ("Next", "Next:34", "Prev", "Prior:33", "Top-L", "Top-R",
           "Bot-L", "Bot-R", "MouseWheel:Down", "MouseWheel:Up")
zoom_buttons = ("Top-L", "Top-R", "Bot-L", "Bot-R")


window = sg.Window(title, layout,
                   return_keyboard_events=True, use_default_focus=False, finalize=True)
graph = window["-GRAPH-"]
graph.draw_image(data, location=(0, 0))
dragging = False
start_point = end_point = prior_rect = None

old_page = 0
old_zoom = 0  

while True:
    event, values = window.read(timeout=100)
    zoom = 0
    force_page = False
    if event == sg.WIN_CLOSED:
        cleanup()
        break

    if event in ("Escape:27",):
        break
    if event[0] == chr(13):
        try:
            cur_page = int(values[0]) - 1
            while cur_page < 0:
                cur_page += page_count
        except:
            cur_page = 0
        goto.update(str(cur_page + 1))


    elif event in ("Next", "Next:34", "MouseWheel:Down"):
        cur_page += 1
    elif event in ("Prev", "Prior:33", "MouseWheel:Up"):
        cur_page -= 1
    elif event == "Top-L":
        zoom = 1
    elif event == "Top-R":
        zoom = 2
    elif event == "Bot-L":
        zoom = 3
    elif event == "Bot-R":
        zoom = 4

    if cur_page >= page_count:
        cur_page = 0
    while cur_page < 0:
        cur_page += page_count

    if cur_page != old_page:
        zoom = old_zoom = 0
        force_page = True

    if event in zoom_buttons:
        if 0 < zoom == old_zoom:
            zoom = 0
            force_page = True

        if zoom != old_zoom:
            force_page = True

    if force_page:
        data = get_page(cur_page, zoom)
        graph.draw_image(data, location=(0,0))
        old_page = cur_page
    old_zoom = zoom

    if event in my_keys or not values[0]:
        goto.update(str(cur_page + 1))
    if event == "-GRAPH-":
        x, y = values["-GRAPH-"]
        if not dragging:
            start_point = (x, y)
            dragging = True
        else:
            end_point = (x, y)
        if prior_rect:
            graph.delete_figure(prior_rect)
        if None not in (start_point, end_point):
            prior_rect = graph.draw_rectangle(start_point, end_point, line_color='red')

    elif event.endswith('+UP'):
        info = window["info"]
        info.update(value=f"grabbed rectangle from {start_point} to {end_point}")
        text = get_text(cur_page, start_point, end_point)
        start_point, end_point = None, None
        dragging = False
        tts = gTTS(text=text, lang='en', slow=False)
        speech_output = os.path.join(final_dir, r"speech.mp3")
        tts.save(speech_output)
        print("Saved")

    if event == "Speak":
        mixer.music.load(speech_output)
        mixer.music.play()
    if event == "Pause":
        mixer.music.pause()
    if event == "Unpause":
        mixer.music.unpause()
    if event == "Stop":
        mixer.music.stop()
        try:
            os.remove(speech_output)
        except:
            pass

    mixer.stop()

window.close()