
# coding: utf-8

# In[19]:


from PIL import Image
import numpy as np
from IPython.display import display, Markdown
from pynq import Xlnk
from pynq import Overlay


# In[20]:


# resize_design = Overlay("bitstream/resize.bit")

resize_design = Overlay("./resize.bit")


# In[21]:


resize_design.ip_dict


# In[22]:


dma = resize_design.axi_dma_0
resizer = resize_design.resize_accel_0


# In[23]:


image_path = "./images/paris.jpg"
original_image = Image.open(image_path)
original_image.load()


# In[24]:


input_array = np.array(original_image)


# In[25]:


input_image = Image.fromarray(input_array)
display(input_image)

def printmd(string):
    display(Markdown('<h1 style="color:DeepPink"> {}</h1>'.format(string)))


# In[26]:


old_width, old_height = original_image.size
printmd("Image size: {}x{} pixels.".format(old_width, old_height))


# In[27]:


resize_factor = 6
new_width, new_height = int(old_width/resize_factor), int(old_height/resize_factor)


# In[28]:


get_ipython().run_cell_magic('timeit', '', 'resized_image_sw = original_image.resize((new_width, new_height), Image.BILINEAR)')


# In[29]:


resized_image_sw = original_image.resize((new_width, new_height), Image.BILINEAR)


# In[30]:


output_array_sw = np.array(resized_image_sw)
result_sw = Image.fromarray(output_array_sw)
display(result_sw)


# In[31]:



width_sw, height_sw = resized_image_sw.size
printmd("Image size resized in SW: {}x{} pixels.".format(width_sw, height_sw))


# In[32]:


xlnk = Xlnk()
in_buffer = xlnk.cma_array(shape=(old_height, old_width, 3), dtype=np.uint8, cacheable=1)
out_buffer = xlnk.cma_array(shape=(new_height, new_width, 3), dtype=np.uint8, cacheable=1)


# In[33]:


in_buffer[:] = input_array
buf_image = Image.fromarray(in_buffer)
display(buf_image)
printmd("Image size: {}x{} pixels.".format(old_width, old_height))


# In[34]:


resizer.write(0x10, old_height) # src rows
resizer.write(0x18, old_width)  # src cols
resizer.write(0x20, new_height) # dst rows
resizer.write(0x28, new_width)  # dst cols

def run_kernel():
    dma.sendchannel.transfer(in_buffer)
    dma.recvchannel.transfer(out_buffer)
    resizer.write(0x00,0x81)
    dma.sendchannel.wait()
    dma.recvchannel.wait()

run_kernel()

result = Image.fromarray(out_buffer)
display(result)
printmd("Resized in Hardware(PL): {}x{} pixels.".format(new_width, new_height))


# In[35]:


get_ipython().run_cell_magic('timeit', '', '\nresizer.write(0x10, old_height) # src rows\nresizer.write(0x18, old_width)  # src cols\nresizer.write(0x20, new_height) # dst rows\nresizer.write(0x28, new_width)  # dst cols\n\ndef run_kernel():\n    dma.sendchannel.transfer(in_buffer)\n    dma.recvchannel.transfer(out_buffer)\n    resizer.write(0x00,0x81)\n    dma.sendchannel.wait()\n    dma.recvchannel.wait()\n\nrun_kernel()')


# In[36]:


xlnk.xlnk_reset()

