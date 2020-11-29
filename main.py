import sys
import fitz
import PySimpleGUI as sg
from sys import exit
import os
import glob
import re

sg.theme('GreenTan')

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

# storage for page display lists
dlist_tab = [None] * page_count

title = "PyMuPDF display of '%s', pages: %i" % (fname, page_count)

curr_dir = os.getcwd()
final_dir = os.path.join(curr_dir, 'software')
if not os.path.exists(final_dir):
    os.makedirs(final_dir)
print(curr_dir)
print(final_dir)
image_dir = glob.glob(final_dir)
for file_name in os.listdir(final_dir):
    # print(file_name)
    filepath = os.path.join(final_dir, file_name)
    os.chmod(filepath, 0o777)
    os.remove(filepath)


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
    # print(output)
    return output  # return the PNG image


def get_text(pno, start_pt, end_pt):
    # dlist = dlist_tab[pno]  # get display list
    # if not dlist:  # create if not yet there
    #     dlist_tab[pno] = doc[pno].getDisplayList()
    #     dlist = dlist_tab[pno]
    page = doc.loadPage(pno)
    # text = page.getText()
    text = page.getTextbox(fitz.Rect(start_pt[0], start_pt[1], end_pt[0], end_pt[1]))
    print(start_pt[0], start_pt[1], end_pt[0], end_pt[1])
    # print(text)
    # col = fitz.utils.getColor("PURPLE")
    # page.drawRect(fitz.Rect(start_pt[0], start_pt[1], end_pt[0], end_pt[1]), color=col, fill=col, overlay=False)
    # t = page.getTextbox(fitz.Rect(start_pt[0], start_pt[1], end_pt[0], end_pt[1]))
    # zoom_x = 2.0
    # zoom_y = 2.0
    # mat = fitz.Matrix(zoom_x,zoom_y)
    # pix = page.getPixmap(matrix=mat)
    # output = os.path.join(final_dir, r"image_to_read.png")
    # pix.writePNG(output)
    pattern = "\[\d+\]\,*\ "
    x = re.findall(pattern, text)
    # print(x)
    text = re.sub(pattern, "", text)
    # print(text)
    return text



cur_page = 0
data = get_page(cur_page)  # show page 1 for start
# image_elem = sg.Image(data=data)

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
    change_submits=True,  # mouse click events
    background_color='lightblue',
    drag_submits=True),],
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
old_zoom = 0  # used for zoom on/off
# the zoom buttons work in on/off mode.

while True:
    event, values = window.read(timeout=100)
    zoom = 0
    force_page = False
    if event == sg.WIN_CLOSED:
        break

    if event in ("Escape:27",):  # this spares me a 'Quit' button!
        break
    if event[0] == chr(13):  # surprise: this is 'Enter'!
        try:
            cur_page = int(values[0]) - 1  # check if valid
            while cur_page < 0:
                cur_page += page_count
        except:
            cur_page = 0  # this guy's trying to fool me
        goto.update(str(cur_page + 1))
        # goto.TKStringVar.set(str(cur_page + 1))

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

    # sanitize page number
    if cur_page >= page_count:  # wrap around
        cur_page = 0
    while cur_page < 0:  # we show conventional page numbers
        cur_page += page_count

    # prevent creating same data again
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
        print(cur_page)
        data = get_page(cur_page, zoom)
        graph.draw_image(data, location=(0,0))
        old_page = cur_page
    old_zoom = zoom

    # update page number field
    if event in my_keys or not values[0]:
        goto.update(str(cur_page + 1))
        # goto.TKStringVar.set(str(cur_page + 1))
    if event == "-GRAPH-":  # if there's a "Graph" event, then it's a mouse
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

    elif event.endswith('+UP'):  # The drawing has ended because mouse up
        info = window["info"]
        info.update(value=f"grabbed rectangle from {start_point} to {end_point}")
        print(start_point, end_point)
        text = get_text(cur_page, start_point, end_point)
        start_point, end_point = None, None  # enable grabbing a new rect
        dragging = False
        print(text)
    
    # if None not in (start_point, end_point):
    #     print("not none")


# import PySimpleGUI as sg
# import string
# import os
# import glob
# import fitz
# import re
# from PIL import Image
# import pytesseract

# def get_page_numbers(value):
#     # print(value)
#     value = value.translate({ord(c): None for c in string.whitespace})
#     # print(value)
#     if '-' in value:
#         first_page_number = int(value.split('-')[0])
#         last_page_number = int(value.split('-')[1])
#     else:
#         first_page_number = int(value)
#         last_page_number = -1
#     return first_page_number, last_page_number


# def main():
#     # layout = [[sg.Text("Choose file"), sg.Input(), sg.FileBrowse()],
#     #           [sg.Text("Enter Pasge Numbers seperated by - "), sg.InputText()],
#     #           [sg.Button("OK"), sg.Button("CANCEL")]]
#     # window = sg.Window("Input", layout)
#     # while True:
#     #     event, values = window.read()
#     #     # print(event, values)
#     #     if event == sg.WIN_CLOSED or event == "CANCEL":
#     #         print("Exiting")
#     #         exit()
#     #         window.close()
#     #     if event == "OK":
#     #         # if values[0] == "":
#     #         #     sg.Popup("Enter PDF file")
#     #         # elif values[1] == "":
#     #         #     sg.Popup("Enter page number(s)")
#     #         # elif values[0] != "" and values[1] != "":
#     #         #     # print("You entered : ", values[0], " ", values[1])
#     #         #     break
#     #         if values[0] != "" or values[1] != "":
#     #             break
#     # window.close()
#     # print("You entered : ", values[0], " ", values[1])
#     # first_page_no, last_page_no = get_page_numbers(values[1])
#     # print("1st page number : ", first_page_no)
#     # print("Last page number : ", last_page_no)

#     curr_dir = os.getcwd()
#     final_dir = os.path.join(curr_dir, 'software')
#     if not os.path.exists(final_dir):
#         os.makedirs(final_dir)
#     print(curr_dir)
#     print(final_dir)
#     image_dir = glob.glob(final_dir)
#     for file_name in os.listdir(final_dir):
#         # print(file_name)
#         filepath = os.path.join(final_dir, file_name)
#         os.chmod(filepath, 0o777)
#         os.remove(filepath)
    
#     pdf_file = fitz.open("test_paper.pdf")
#     first_page_no, last_page_no = 2, -1
#     if last_page_no == -1:
#         page = pdf_file.loadPage(first_page_no - 1)
#         # mat = 
#         # font_list = pdf_file.getPageFontList(first_page_no)
#         # text = pdf_file.getPageText(first_page_no)
#         text = page.getText()
#         # print(page.links())
#         pattern = "\[\d+\]"
#         links = page.getLinks()
#         t = page.getText()
#         # x = re.findall(pattern, t)
#         f = page.getFontList()
#         print(page.rect)
#         col = fitz.utils.getColor("PURPLE")
#         page.drawRect(fitz.Rect(44.0, 374.0, 309.0, 681.0), color=col, fill=col, overlay=False)
#         t = page.getTextbox(fitz.Rect(44.0, 374.0, 309.0, 681.0))
#         zoom_x = 2.0
#         zoom_y = 2.0
#         mat = fitz.Matrix(zoom_x,zoom_y)
#         pix = page.getPixmap(matrix=mat)
#         output = os.path.join(final_dir, r"image_to_read.png")
#         pix.writePNG(output)
    
#     print(t)
#     # for i in t[0]:
#     #     print(t)
#     # print(x)
#     # print(f)

#     # for file in os.listdir(final_dir):
#     #     data = pytesseract.image_to_string(Image.open(os.path.join(final_dir,file)),lang="eng")
#     #     data = data.replace("|","I") # For some reason the image to text translation would put | instead of the letter I. So we replace | with I
#     #     data = data.split('\n')
#     #     mytext.append(data)

#     # print(mytext)

#     # print(font_list)
#     # print(text)
#     # for link in links:
#     #     print(link)



# if __name__ == "__main__":
#     main()