from tkinter import *

root = Tk()

root.title("Product uploader")
root.attributes('-alpha', 0.8)
root.geometry("800x450-100+100")

label = Label(root, text="Hello World", font=("Helvetica", 16))
label.pack()

root.mainloop()