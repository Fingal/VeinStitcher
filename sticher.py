from stack_io import *
import wx
import wx.lib.scrolledpanel
from itertools import product
from math import floor, ceil
import PIL


TEST=False

def tprint(*args,**kwargs):
    if TEST:
        print(*args,**kwargs)

def PIL2wx (image):
    width, height = image.size
    return wx.Bitmap.FromBuffer(width, height, image.tobytes())

def get_slice(array,dim):
    return array[dim[0][0]:dim[1][0],dim[0][1]:dim[1][1],dim[0][2]:dim[1][2]]

def tuple_add(a,b):
    return tuple(i+j for i,j in zip(a,b))

def tuple_sup(a,b):
    return tuple(i-j for i,j in zip(a,b))

class ImagePanel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent,array,func,**kwargs):
        tprint(kwargs.get('size'))
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, **kwargs)
        self.SetupScrolling()
        self.on_rectangle=func
        self.parent=parent
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.vbox)
        self.array=np.minimum(array,4000)
        png = PIL2wx(get_image(array,0))
        self.img=wx.StaticBitmap(self, -1, png)
        self.vbox.Add(self.img)

        self.slider=wx.Slider(self, minValue=0, maxValue=self.array.shape[2]-1, name='height',size=(self.img.GetSize()[0],20))
        self.Bind(wx.EVT_SCROLL, self.on_slide, self.slider)
        self.vbox.Add(self.slider)
        
        self.img.Bind(wx.EVT_LEFT_DOWN,self.on_down_mouse)
        self.img.Bind(wx.EVT_LEFT_UP,self.on_up_mouse)

        self.layer_label=wx.StaticText(self, label='0')
        self.vbox.Add(self.layer_label)

        self.img.Bind(wx.EVT_LEFT_UP,self.on_up_mouse)

        
        dc = wx.ClientDC(self.img)
        self.overlay=wx.Overlay()
        odc = wx.DCOverlay(self.overlay, dc)


    def on_slide(self,event):
        self.layer_label.SetLabel(str(self.slider.GetValue()))
        self.set_image(self.slider.GetValue())
    
    def set_image(self,height):
        png = PIL2wx(get_image(self.array,height))
        self.img.SetBitmap(png)

    def on_down_mouse(self, event):
        self.start_pos = event.GetPosition()    
        tprint(self.start_pos)

    def on_up_mouse(self, event):
        tprint('aaa')
        end_pos = event.GetPosition()
        if self.on_rectangle:
            self.on_rectangle(tuple(reversed(self.start_pos)),tuple(reversed(end_pos)),self.slider.GetValue())
    # import pdb; pdb.set_trace()




class StichFrame(wx.Frame):
    def __init__(self, arrays,translations,secondary_files=[],array_history=[], parent=None):
        self.secondary_files=secondary_files
        self.size = (1280, 880)
        wx.Frame.__init__(self, None,size=self.size)
        self.parent=parent
        self.box = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.box)
        trans_vec=translations[0]
        source,target=arrays
        self.result,self.array_history = self.combine_arrays(source,target,trans_vec,array_history)

        self.box.Add(ImagePanel(self,self.result,None,size=(self.result.shape[1]+10,self.result.shape[0]+100)), wx.EXPAND | wx.ALL)

        box2=wx.BoxSizer(wx.VERTICAL)
        self.box.Add(box2)


        self.directory_field=LoadFilePanel(self,button_label='Add pi File')
        box2.Add(self.directory_field, wx.EXPAND | wx.ALL)
        self.secondary_field=LoadFilePanel(self,button_label='Add dr File')
        box2.Add(self.secondary_field, wx.EXPAND | wx.ALL)

        box3 = wx.BoxSizer(wx.HORIZONTAL)
        box2.Add(box3)

        self.save_button = wx.Button(self, label="Save File")
        box3.Add(self.save_button, wx.EXPAND | wx.ALL)
        self.Bind(wx.EVT_BUTTON, self.save_file, self.save_button)

        self.load_button = wx.Button(self, label="Load another file")
        box3.Add(self.load_button, wx.EXPAND | wx.ALL)
        self.Bind(wx.EVT_BUTTON, self.load_file, self.load_button)
        self.Show()

    def get_fit_array(self,array_history,array,trans_vec):
        for array,pos_vec in array_history:
            do=False
            for point in [(0,0),(array.shape[0],0),(0,array.shape[1]),array.shape[:2]]:
                if all(np.array(pos_vec[:2])<np.array(trans_vec[:2])+np.array(point)) and all(np.array(trans_vec[:2])+np.array(point)<(np.array(pos_vec[:2])+np.array(array.shape[:2]))):
                    do=True
            if do:
                yield np.array(trans_vec)-np.array(pos_vec),array
        

    def fit_concentration(self,trans_vec,source,target):
        s_trans_vec=tuple(max(0,-i) for i in trans_vec)
        t_trans_vec=tuple(max(0,i) for i in trans_vec)
        a=source[t_trans_vec[0]:target.shape[0]-s_trans_vec[0],t_trans_vec[1]:target.shape[1]-s_trans_vec[1],:]
        b=target[s_trans_vec[0]:source.shape[0]-t_trans_vec[0],s_trans_vec[1]:source.shape[1]-t_trans_vec[1],:]
        if a.shape[:2]==b.shape[:2]:
            for i in range(target.shape[2]):
                try:
                    s_index = t_trans_vec[2]+i
                    t_index = s_trans_vec[2]+i
                    essential=np.logical_and(a[:,:,s_index]<3900,np.logical_and(b[:,:,t_index]<3900,np.logical_and(a[:,:,s_index]>200,b[:,:,t_index]>200))).astype(np.uint8)
                    ratio=np.sum(a[:,:,s_index]*essential)/np.sum(b[:,:,t_index]*essential)
                    a_max=np.max(a)
                    b_max=np.max(b)
                    new_ratio=np.sum(np.minimum(a[:,:,s_index],b_max*ratio)*essential)/np.sum(np.minimum(b[:,:,t_index],a_max/ratio)*essential)
                    tprint('layer',s_index,t_index)
                    while abs(ratio-new_ratio)>0.001:
                        ratio=new_ratio
                        new_ratio=np.sum(np.minimum(a[:,:,s_index],b_max*ratio)*essential)/np.sum(np.minimum(b[:,:,t_index],a_max/ratio)*essential)
                        tprint('  ',ratio)
                    target[:,:,t_index]=target[:,:,t_index]*ratio
                except IndexError:
                    tprint(i,'IndexError')
        else:
            print(a.shape,b.shape)
            print(trans_vec)
        return target


    def combine_arrays(self,source : np.array,target : np.array,trans_vec,array_history):
        sum_dim=tuple([max(a+max(-v,0),b+max(v,0)) for a,b,v in zip(source.shape,target.shape,trans_vec)])
        tprint(sum_dim)
        result = np.zeros(sum_dim)
        s_trans_vec=tuple(max(0,-i) for i in trans_vec)
        t_trans_vec=tuple(max(0,i) for i in trans_vec)
        for vec,array in self.get_fit_array(array_history,target,trans_vec):
            target=self.fit_concentration(vec,array,target)

        take1_6=True
        if take1_6:
            result[s_trans_vec[0]:s_trans_vec[0]+source.shape[0],s_trans_vec[1]:s_trans_vec[1]+source.shape[1],s_trans_vec[2]:s_trans_vec[2]+source.shape[2]]=source
            result[t_trans_vec[0]:t_trans_vec[0]+target.shape[0],t_trans_vec[1]:t_trans_vec[1]+target.shape[1],t_trans_vec[2]:t_trans_vec[2]+target.shape[2]]=target
        else:
            result[s_trans_vec[0]:s_trans_vec[0]+source.shape[0],s_trans_vec[1]:s_trans_vec[1]+source.shape[1],s_trans_vec[2]:s_trans_vec[2]+source.shape[2]]=target
            result[t_trans_vec[0]:t_trans_vec[0]+target.shape[0],t_trans_vec[1]:t_trans_vec[1]+target.shape[1],t_trans_vec[2]:t_trans_vec[2]+target.shape[2]]=source



        array_history=[(arr,tuple_add(vec,s_trans_vec)) for arr,vec in array_history]
        array_history.append((target,t_trans_vec))

        result=result.astype(source.dtype)
        return result,array_history



    def save_file(self,event):
        # #(270, 'ImageDescription')
        # metadata = self.parent.img1.tag

        # # self.parent.img1.tag
        # # metadata[282]=self.parent.img1.tag[282]
        # # metadata[283]=self.parent.img1.tag[283]

        # metadata[256]=(self.result.shape[1],)
        # metadata[257]=(self.result.shape[0],)


        # slices=self.result.shape[2]
        # spacing = get_dimentions(self.parent.img1)[-1]
        # vmax = np.max(self.result)
        # metadata[270]=(f'ImageJ=1.50e\nimages={slices}\nslices={slices}\nunit=micron\nspacing={spacing:.7f}\nloop=false\nmin=0.0\nmax={vmax:.1f}\n',)
        saveFileDialog = wx.FileDialog(
            self,
            "Save",
            "",
            "",
            "Tiff files (*.tif)|*.tif*|Any type (*.*)|*.*",
            wx.FD_SAVE| wx.FD_OVERWRITE_PROMPT,
        )

        if saveFileDialog.ShowModal() == wx.ID_CANCEL:
            return     # the user changed their mind
        path=saveFileDialog.GetPath()
        saveFileDialog.Destroy()
        tprint(path)
        if 'tif' not in path[-4:]: 
            tprint('add tiff type')
            path=path+'.tif'
        name,ext=path.split('.')

        save_stack(self.result,name=name+'_pi.'+ext)

        base_array = image_to_array(Image.open(self.secondary_files[0]))
        array_history=[(base_array,(0,0,0))]
        for file,trans_vec in self.secondary_files[1:]:
            array = image_to_array(Image.open(file))
            base_array,array_history = self.combine_arrays(base_array,array,trans_vec,array_history)
        save_stack(base_array,name=name+'_dr.'+ext)        


    def load_file(self,event):
        file_name = self.directory_field.directory_field.GetValue()
        sceondary_file=self.secondary_field.directory_field.GetValue()

        #if os.path.isfile(file_name_1) and os.path.isfile(file_name_2) and os.path.isfile(secondary_files[0]) and os.path.isfile(secondary_files[1]):
        if os.path.isfile(file_name) and os.path.isfile(sceondary_file):
            
            img=Image.open(file_name)
            ComareFrame(self.result,img,self.secondary_files+[sceondary_file],is_array=True,array_history=self.array_history)
            self.parent.Close()
            self.parent=None

        # openFileDialog = wx.FileDialog(
        #     self,
        #     "Open",
        #     "",
        #     "",
        #     "Tiff files (*.tif)|*.tif*|Any type (*.*)|*.*",
        #     wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        # )
        # if openFileDialog.ShowModal() == wx.ID_CANCEL:
        #     return     # the user changed their mind
        # path = openFileDialog.GetPath()
        # openFileDialog.Destroy()

        # img=Image.open(path)
        # ComareFrame(self.result,img,secondary_files=self.secondary_files,is_array=True)
        # self.parent.Close()

        



class PopupFrame(wx.Frame):
    def __init__(self, array, parent=None):
        wx.Frame.__init__(self, parent=parent)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.hbox)
        self.hbox.Add(ImagePanel(self,array,None), wx.EXPAND | wx.ALL)
        self.Show()

class ComareFrame(wx.Frame):
    def __init__(self,img1,img2,secondary_files=[],array_history=[],is_array=False):
        self.array_history=array_history
        self.secondary_files=secondary_files
        self.size = (1280, 880)
        wx.Frame.__init__(
            self,
            None,
            style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE,
        )
        if not is_array:
            self.img1=img1
            self.img2=img2
            self.SetMinSize(self.size)
            self.source = array = image_to_array(img1)
            self.target = array = image_to_array(img2)
        else:
            self.source = img1

            self.img2=img2
            self.target = array = image_to_array(img2)


        # self.panel = wx.Panel(self)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.hbox)
        # self.canvas = mockup.OpenGLCanvasMockup(self)
        self.hbox.Add(ImagePanel(self,self.source,self.set_rectangle,size=(self.source.shape[1]+10,self.source.shape[0]+50)), wx.EXPAND | wx.ALL)
        
        self.hbox.Add(ImagePanel(self,self.target,self.fit,size=(self.target.shape[1]+10,self.target.shape[0]+50)), wx.EXPAND | wx.ALL)

        self.hbox.Add(wx.CheckBox(), wx.EXPAND | wx.ALL)
        self.Show()
  
    
    def set_rectangle(self,start_pos,end_pos,height):
        temp_cube = ((start_pos)+(height-8,),(end_pos)+(height+8,))
        self.cube = (tuple(map(min,zip(*temp_cube))),tuple(map(max,zip(*temp_cube))))
        self.slice = get_slice(self.source,self.cube)
        #PopupFrame(self.slice)

    
    def fit(self,start_pos,end_pos,height):
        pos = None
        diff = None
        self.range = tuple(zip((start_pos)+(max(0,height-5),),(end_pos)+(min(self.target.shape[2],height+6),)))
        if self.cube:
            tprint(self.cube)
            tprint(self.range)
            dim = tuple(map(lambda x: x[1]-x[0],zip(*self.cube)))
            tprint(('dim',dim))
            for x in range(*self.range[0]):
                for y in range(*self.range[1]):
                    for z in range(*self.range[2]):
                        target_cube = self.target[x-floor(dim[0]/2):x+ceil(dim[0]/2),y-floor(dim[1]/2):y+ceil(dim[1]/2),z-floor(dim[2]/2):z+ceil(dim[2]/2)]
                        if target_cube.shape==self.slice.shape:
                            target_cube=np.maximum(target_cube - (target_cube<300).astype(int)*300,0)
                            s=np.maximum(self.slice - (self.slice<300).astype(int)*300,0)
                            s=s.astype(np.int64)
                            target_cube=target_cube.astype(np.int64)
                            temp_diff = np.sum((target_cube-s)**2)
                            #define new step on close

                            #PopupFrame(target_cube)
                            #import time; time.sleep(3)
                            if diff == None or diff>temp_diff:
                                diff = temp_diff
                                pos = (x,y,z)
                                tprint(temp_diff)
                                tprint(x,y,z)
        else:
            print("no cube")
                        
        tprint(diff)
        pos2 = tuple([i+floor(d/2) for i,d in zip(self.cube[0],dim)])
        tprint(pos2)
        pos2 = tuple([i-ceil(d/2) for i,d in zip(self.cube[1],dim)])
        tprint(pos2)
        tprint(pos)
        x,y,z = pos
        target_cube = self.target[x-floor(dim[0]/2):x+ceil(dim[0]/2),y-floor(dim[1]/2):y+ceil(dim[1]/2),z-floor(dim[2]/2):z+ceil(dim[2]/2)]
        #PopupFrame(target_cube)
        trans_vec = tuple_sup(pos2,pos)
        self.secondary_files=self.secondary_files[:-1]+[(self.secondary_files[-1],trans_vec)]
        if not self.array_history:
            array_history=[(self.source,(0,0,0))]
        else:
            array_history=self.array_history

        StichFrame([self.source,self.target],[trans_vec],secondary_files=self.secondary_files,array_history=array_history,parent=self)

    def on_resize(self, event):
        pass
        tprint(self.size)

    def on_close(self, event):
        self.Destroy()
        sys.exit(0)

class LoadFilePanel(wx.Panel):
    def __init__(self,parent,button_label='',def_text='',**kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        self.sizer = wx.GridBagSizer(3, 3)
        self.SetSizer(self.sizer)
        self.directory_field = wx.TextCtrl(self,value=def_text)
        self.directory_field.SetToolTip("Directory")
        self.sizer.Add(
            self.directory_field,
            pos=(0, 0),
            span=(1, 35),
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=5,
        )

        self.open_button = wx.Button(self, label=button_label)
        self.sizer.Add(
            self.open_button,
            pos=(0, 35),
            span=(1, 2),
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=5,
        )
        self.Bind(wx.EVT_BUTTON, self.open_dialog(self.directory_field), self.open_button)

    def open_dialog(self,directory_field):
        def f(event):
            openFileDialog = wx.FileDialog(
                self,
                "Open",
                "",
                "",
                "Tiff files (*.tif)|*.tif*|Any type (*.*)|*.*",
                wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            )

            openFileDialog.ShowModal()
            directory_field.SetLabelText(openFileDialog.GetPath())
            openFileDialog.Destroy()
        return f

class MyFrame(wx.Frame):
    def __init__(self):
        self.size = (1280, 880)
        wx.Frame.__init__(
            self,
            None, size=(1200,300)
        )
        self.sizer = wx.GridBagSizer(3, 3)
        self.SetSizer(self.sizer)
        self.directory_field_1 = LoadFilePanel(self,button_label="Add pi file", def_text="D:\\symulacje\\stacks_vascular_1\\stacks_vascular_1\\xp5_dr3\\dr3_2_pi.tif" if TEST else '')
        self.sizer.Add(
            self.directory_field_1,
            pos=(1, 0),
            span=(1, 12),
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=5,
        )
        self.secndary_field_1 = LoadFilePanel(self,button_label="Add dr file", def_text="D:\\symulacje\\stacks_vascular_1\\stacks_vascular_1\\xp5_dr3\\dr3_2_dr.tif"  if TEST else '')
        self.sizer.Add(
            self.secndary_field_1,
            pos=(1, 12),
            span=(1, 12),
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=5,
        )
        self.directory_field_2 = LoadFilePanel(self,button_label="Add pi file", def_text="D:\\symulacje\\stacks_vascular_1\\stacks_vascular_1\\xp5_dr3\\dr3_3_pi.tif" if TEST else '')
        self.sizer.Add(
            self.directory_field_2,
            pos=(2, 0),
            span=(1, 12),
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=5,
        )
        self.secndary_field_2 = LoadFilePanel(self,button_label="Add dr file", def_text="D:\\symulacje\\stacks_vascular_1\\stacks_vascular_1\\xp5_dr3\\dr3_3_dr.tif" if TEST else '')
        self.sizer.Add(
            self.secndary_field_2,
            pos=(2, 12),
            span=(1, 12),
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=5,
        )

        self.load_button = wx.Button(self, label="Load")
        self.sizer.Add(
            self.load_button,
            pos=(3, 0),
            span=(1, 2),
            flag=wx.EXPAND | wx.LEFT | wx.RIGHT,
            border=5,
        )
        self.Bind(wx.EVT_BUTTON, self.load_file, self.load_button)
        self.Show()

    def open_dialog(self,directory_field):
        def f(event):
            openFileDialog = wx.FileDialog(
                self,
                "Open",
                "",
                "",
                "Tiff files (*.tif)|*.tif*|Any type (*.*)|*.*",
                wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
            )

            openFileDialog.ShowModal()
            directory_field.SetLabelText(openFileDialog.GetPath())
            openFileDialog.Destroy()
        return f

    def load_file(self, event):
        file_name_1 = self.directory_field_1.directory_field.GetValue()
        file_name_2 = self.directory_field_2.directory_field.GetValue()
        secondary_files=[self.secndary_field_1.directory_field.GetValue(),self.secndary_field_2.directory_field.GetValue()]

        if os.path.isfile(file_name_1) and os.path.isfile(file_name_2) and os.path.isfile(secondary_files[0]) and os.path.isfile(secondary_files[1]):
        #if os.path.isfile(file_name_1) and os.path.isfile(file_name_2):
            img1=Image.open(file_name_1)
            img2=Image.open(file_name_2)


            ComareFrame(img1,img2,secondary_files)
            


class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame()
        frame.Show()
        return True


if __name__ == "__main__":
    # import cProfile
    # cProfile.run('MyApp().MainLoop()')
    app = MyApp()
    app.MainLoop()
