"""
ODR app, programa para hacer ajustes por Orthogonal Distance Regresion
Copyright (C) 2026  Eduardo López

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Interfaz Gráfica para ayudar a hacer ajustes ODR.

V1.0 del 26/08/24 -- Rutina inicial e interfaz simple, solo se pueden hacer
                     ajustes polinomiales

V1.1 del 04/05/26 -- Se optimiza la rutina para que funcione bien en linux

V1.2 del 08/09/26 -- Se modifica el programa para funcionar en win y en linux
                     por igual. 

"""

import wx
import wx.grid
from matplotlib.backends.backend_wxagg import (FigureCanvasWxAgg as FigureCanvas,
NavigationToolbar2WxAgg as NavigationToolbar)
from matplotlib.figure import Figure
from scipy.odr import Model, RealData, ODR, polynomial
from numpy import polyfit, poly1d, linspace
import sys
import os
from platform import system


 
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

#clase para la tabla optimizada
class Grid_opt(wx.grid.Grid):
    def __init__(self, parent):
        wx.grid.Grid.__init__(self, parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key)
        # self.Bind(wx.grid.EVT_GRID_CELL_CHANGING, self.on_change)
        self.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.on_cell_right_click)
        self.selected_rows = []
        self.selected_cols = []
        self.history = []
        self.EnableScrolling(False, True)

    def get_col_headers(self):
        return [self.GetColLabelValue(col) for col in range(self.GetNumberCols())]

    def get_table(self):
        for row in range(self.GetNumberRows()):
            result = {}
            for col, header in enumerate(self.get_col_headers()):
                result[header] = self.GetCellValue(row, col)
            yield result

    def add_rows(self, event):
        for row in self.selected_rows:
            self.InsertRows(row)
        self.add_history({"type": "add_rows", "rows": self.selected_rows})

    def delete_rows(self, event):
        self.cut(event)
        rows = []
        for row in reversed(self.selected_rows):
            rows.append((
                row,
                {  # More attributes can be added
                    "label": self.GetRowLabelValue(row),
                    "size": self.GetRowSize(row)
                }
            ))
            self.DeleteRows(row)
        self.add_history({"type": "delete_rows", "rows": rows})

    def add_cols(self, event):
        for col in self.selected_cols:
            self.InsertCols(col)
        self.add_history({"type": "add_cols", "cols": self.selected_cols})

    def delete_cols(self, event):
        self.delete(event)
        cols = []
        for col in reversed(self.selected_cols):
            cols.append((
                col,
                {  # More attributes can be added
                    "label": self.GetColLabelValue(col),
                    "size": self.GetColSize(col)
                }
            ))
            self.DeleteCols(col)
        self.add_history({"type": "delete_cols", "cols": cols})

    def on_cell_right_click(self, event):
        menus = [(wx.Window.NewControlId(), "Cut", self.cut),
                 (wx.Window.NewControlId(), "Copy", self.copy),
                 (wx.Window.NewControlId(), "Paste", self.paste)]
        popup_menu = wx.Menu()
        for menu in menus:
            if menu is None:
                popup_menu.AppendSeparator()
                continue
            popup_menu.Append(menu[0], menu[1])
            self.Bind(wx.EVT_MENU, menu[2], id=menu[0])

        self.PopupMenu(popup_menu, event.GetPosition())
        popup_menu.Destroy()
        return


    def on_change(self, event):
        cell = event.GetEventObject()
        row = cell.GetGridCursorRow()
        col = cell.GetGridCursorCol()
        attribute = {"value": self.GetCellValue(row, col)}
        self.add_history({"type": "change", "cells": [(row, col, attribute)]})

    def add_history(self, change):
        self.history.append(change)

    def undo(self):
        if not len(self.history):
            return

        action = self.history.pop()
        if action["type"] == "change" or action["type"] == "delete":
            for row, col, attribute in action["cells"]:
                self.SetCellValue(row, col, attribute["value"])
                if action["type"] == "delete":
                    self.SetCellAlignment(row, col, *attribute["alignment"])  # *attribute["alignment"] > horiz, vert

        elif action["type"] == "delete_rows":
            for row, attribute in reversed(action["rows"]):
                self.InsertRows(row)
                self.SetRowLabelValue(row, attribute["label"])
                self.SetRowSize(row, attribute["size"])

        elif action["type"] == "delete_cols":
            for col, attribute in reversed(action["cols"]):
                self.InsertCols(col)
                self.SetColLabelValue(col, attribute["label"])
                self.SetColSize(col, attribute["size"])

        elif action["type"] == "add_rows":
            for row in reversed(action["rows"]):
                self.DeleteRows(row)

        elif action["type"] == "add_cols":
            for col in reversed(action["cols"]):
                self.DeleteCols(col)
        else:
            return

    def on_key(self, event):
        """
        Handles all key events.
        """
        # print(event.GetKeyCode())
        # Ctrl+C or Ctrl+Insert
        if event.ControlDown() and event.GetKeyCode() in [67, 322]:
            self.copy(event)

        # Ctrl+V
        elif event.ControlDown() and event.GetKeyCode() == 86:
            self.paste(event)

        # DEL
        elif event.GetKeyCode() == 127:
            self.delete(event)

        # Ctrl+A
        elif event.ControlDown() and event.GetKeyCode() == 65:
            self.SelectAll()

        # Ctrl+Z
        # elif event.ControlDown() and event.GetKeyCode() == 90:
        #     self.undo()

        # Ctrl+X
        elif event.ControlDown() and event.GetKeyCode() == 88:
            # Call delete method
            self.cut(event)

        # Ctrl+V or Shift + Insert
        elif (event.ControlDown() and event.GetKeyCode() == 67) \
                or (event.ShiftDown() and event.GetKeyCode() == 322):
            self.paste(event)

        else:
            event.Skip()

    def get_selection(self):
        """
        Returns selected range's start_row, start_col, end_row, end_col
        If there is no selection, returns selected cell's start_row=end_row, start_col=end_col
        """
        if not len(self.GetSelectionBlockTopLeft()):
            selected_columns = self.GetSelectedCols()
            selected_rows = self.GetSelectedRows()
            if selected_columns:
                start_col = selected_columns[0]
                end_col = selected_columns[-1]
                start_row = 0
                end_row = self.GetNumberRows() - 1
            elif selected_rows:
                start_row = selected_rows[0]
                end_row = selected_rows[-1]
                start_col = 0
                end_col = self.GetNumberCols() - 1
            else:
                start_row = end_row = self.GetGridCursorRow()
                start_col = end_col = self.GetGridCursorCol()
        elif len(self.GetSelectionBlockTopLeft()) > 1:
            wx.MessageBox("Multiple selections are not supported", "Warning")
            return []
        else:
            start_row, start_col = self.GetSelectionBlockTopLeft()[0]
            end_row, end_col = self.GetSelectionBlockBottomRight()[0]

        return [start_row, start_col, end_row, end_col]

    def get_selected_cells(self):
        # returns a list of selected cells
        selection = self.get_selection()
        if not selection:
            return

        start_row, start_col, end_row, end_col = selection
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                yield [row, col]

    def copy(self, event):
        """
        Copies range of selected cells to clipboard.
        """

        selection = self.get_selection()
        if not selection:
            return []
        start_row, start_col, end_row, end_col = selection

        data = u''

        rows = range(start_row, end_row + 1)
        for row in rows:
            columns = range(start_col, end_col + 1)
            for idx, column in enumerate(columns, 1):
                if idx == len(columns):
                    # if we are at the last cell of the row, add new line instead
                    data += self.GetCellValue(row, column) + "\n"
                else:
                    data += self.GetCellValue(row, column) + "\t"

        text_data_object = wx.TextDataObject()
        text_data_object.SetText(data)

        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(text_data_object)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Can't open the clipboard", "Warning")

    def paste(self, event):
        if not wx.TheClipboard.Open():
            wx.MessageBox("Can't open the clipboard", "Warning")
            return False

        clipboard = wx.TextDataObject()
        wx.TheClipboard.GetData(clipboard)
        wx.TheClipboard.Close()
        data = clipboard.GetText()
        if data[-1] == "\n":
            data = data[:-1]

        try:
            cells = self.get_selected_cells()
            cell = next(cells)
        except StopIteration:
            return False

        start_row = end_row = cell[0]
        start_col = end_col = cell[1]
        max_row = self.GetNumberRows()
        max_col = self.GetNumberCols()

        history = []
        out_of_range = False

        for row, line in enumerate(data.split("\n")):
            target_row = start_row + row
            if not (0 <= target_row < max_row):
                out_of_range = True
                break

            if target_row > end_row:
                end_row = target_row

            for col, value in enumerate(line.split("\t")):
                target_col = start_col + col
                if not (0 <= target_col < max_col):
                    out_of_range = True
                    break

                if target_col > end_col:
                    end_col = target_col

                # save previous value of the cell for undo
                history.append([target_row, target_col, {"value": self.GetCellValue(target_row, target_col)}])

                self.SetCellValue(target_row, target_col, value)

        self.SelectBlock(start_row, start_col, end_row, end_col)  # select pasted range
        if out_of_range:
            wx.MessageBox("Pasted data is out of Grid range", "Warning")

        self.add_history({"type": "change", "cells": history})

    def delete(self, event):
        cells = []
        for row, col in self.get_selected_cells():
            attributes = {
                "value": self.GetCellValue(row, col),
                "alignment": self.GetCellAlignment(row, col)
            }
            cells.append((row, col, attributes))
            self.SetCellValue(row, col, "")

        self.add_history({"type": "delete", "cells": cells})

    def cut(self, event):
        self.copy(event)
        self.delete(event)

#clase para generar las gráficas
class graph_plt(wx.Panel):
    def __init__(self,parent, X, dX, Y, dY, title='Datos'):
        wx.Panel.__init__(self,parent,-1)

        #generamos la figura
        self.figure = Figure((6.5, 4.0))
        self.axes = self.figure.add_subplot(1, 1, 1)
        
        #configuramos la apariencia de la gràfica
        self.axes.set_xlabel('X')
        self.axes.set_ylabel('Y')        
        self.axes.set_title(title)
        self.axes.grid(visible=True, which='major', axis='y',color='0.8',
                       linestyle='-.', linewidth=0.7)

        #realizamos la gráfica
        self.axes.errorbar(x=X, y=Y, xerr=dX, yerr=dY, fmt='ob')

        

        self.figure.tight_layout()
        self.canvas = FigureCanvas(self, -1,self.figure)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.EXPAND)
        self.SetSizer(self.sizer)
        self.Fit()

        self.add_toolbar()
    
    def add_toolbar(self):
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.SetBackgroundColour((220,117,26))
        self.toolbar.Realize()
        # By adding toolbar in sizer, we are able to put it at the bottom
        # of the frame - so appearance is closer to GTK version.
        self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        # update the axes menu on the toolbar
        self.toolbar.update()



    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        del self.figure, self.axes, self.canvas

#clase para generar las gráficas de los ajustes
class graph_fit(wx.Panel):
    def __init__(self, parent, X, dX, Y, dY, output, grado , title='Ajuste'):
        wx.Panel.__init__(self,parent,-1)

        #generamos la figura
        self.figure = Figure((6.5, 4.0))
        self.axes = self.figure.add_subplot(1, 1, 1)
        
        #configuramos la apariencia de la gràfica
        self.axes.set_xlabel('X')
        self.axes.set_ylabel('Y')        
        self.axes.set_title(title)
        self.axes.grid(visible=True, which='major', axis='y',color='0.8',
                       linestyle='-.', linewidth=0.7)

        #realizamos la gráfica
        self.axes.errorbar(x=X, y=Y, xerr=dX, yerr=dY, fmt='ob')

        #generamos el ajuste
        p_r = poly1d(output.beta[::-1])
        x_a = linspace(X[0]-0.1*X[len(X)-1],1.1*X[len(X)-1],100)
        y_a = p_r(x_a)
        self.axes.plot(x_a, y_a, 'r--', label=self.out_mod(grado, output.beta, output.sd_beta ))
        self.axes.legend(prop={'size': 8})

        self.figure.tight_layout()
        self.canvas = FigureCanvas(self, -1,self.figure)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.EXPAND)
        self.SetSizer(self.sizer)
        self.Fit()

        self.add_toolbar()
    
    def add_toolbar(self):
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.SetBackgroundColour((220,117,26))
        self.toolbar.Realize()
        # By adding toolbar in sizer, we are able to put it at the bottom
        # of the frame - so appearance is closer to GTK version.
        self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        # update the axes menu on the toolbar
        self.toolbar.update()

    #función que genera la etiqueta para la salida.
    def out_mod(self, n, beta, beta_err):
        out = '$ y='
        coef =[]
        xx = []

        for i in range(n+1):
            coef.append('a_%s' % i)
            xx.append('x^%s' % i)

        xx[0] = ''

        for i in range(n+1):
            out = out + ' %s%s ' % (coef[i],xx[i])
            if i < n:
                out = out + '+'
            else:
                out = out + '$\n'

        for i in range(n+1):
            out =  out + '$ ' + coef[i] + ' = %s \\pm %s $\n' % (beta[i], beta_err[i])

        return out
    
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        del self.figure, self.axes, self.canvas


#clase de la app en sí
class ODR_app(wx.Frame):
    #init
    def __init__(self, *args, **kw):
        super(ODR_app, self).__init__(*args, **kw)
        self.Bob()

    #constructor
    def Bob(self):
        #-----------------------------------------------------------------------
        #             Configuración general de la ventana
        #region-----------------------------------------------------------------------
        self.SetTitle('ODR app')
        self.Centre()
        if system() == 'Linux':
            self.SetSize((1120, 730)) #Tamaño de ventana
            bundle = wx.IconBundle()
            bundle.AddIcon(resource_path('odr_app_logo256.png'), wx.BITMAP_TYPE_PNG)
            bundle.AddIcon(resource_path('odr_app_logo128.png'), wx.BITMAP_TYPE_PNG)
            bundle.AddIcon(resource_path('odr_app_logo96.png'), wx.BITMAP_TYPE_PNG)
            bundle.AddIcon(resource_path('odr_app_logo72.png'), wx.BITMAP_TYPE_PNG)
            bundle.AddIcon(resource_path('odr_app_logo64.png'), wx.BITMAP_TYPE_PNG)
            bundle.AddIcon(resource_path('odr_app_logo48.png'), wx.BITMAP_TYPE_PNG)
            bundle.AddIcon(resource_path('odr_app_logo32.png'), wx.BITMAP_TYPE_PNG)
            bundle.AddIcon(resource_path('odr_app_logo24.png'), wx.BITMAP_TYPE_PNG)
            bundle.AddIcon(resource_path('odr_app_logo16.png'), wx.BITMAP_TYPE_PNG)
            self.SetIcons(bundle)

        elif system() == 'Windows':
            self.SetSize((920, 630)) #Tamaño de ventana
            self.SetIcon(wx.Icon(resource_path('odr_app_logo.ico')))

        self.pnl = wx.Panel(self)
        self.pnl.SetBackgroundColour((19, 91, 139))

        #IDs genéricos
        self.ID_FIT = wx.Window.NewControlId()
        self.ID_PLOT = wx.Window.NewControlId()
        #endregion

        #-----------------------------------------------------------------------
        #             Generación de menús
        #region-----------------------------------------------------------------
        #barra de menú
        self.MenuBar = wx.MenuBar()

        #primer menú
        FileMenu = wx.Menu()
        QuitItem = wx.MenuItem(FileMenu, wx.ID_EXIT, '&Cerrar\tCtrl+Q', 'Cerrar la aplicación')
        QuitItem.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_QUIT))
        FileMenu.Append(QuitItem)

        #segundo menú
        HelpMenu = wx.Menu()
        AboutItem = wx.MenuItem(HelpMenu, wx.ID_ABOUT, '&Acerca de ...\tCtrl+U', 'Información sobre la aplicación')
        AboutItem.SetBitmap(wx.ArtProvider.GetBitmap(wx.ART_INFORMATION))
        HelpMenu.Append(AboutItem)

        #se añaden los menús a la barra
        self.MenuBar.Append(FileMenu, '&Archivo')
        self.MenuBar.Append(HelpMenu, 'A&yuda')

        #se añade la barra a la ventana
        self.SetMenuBar(self.MenuBar)
        #endregion

        #-----------------------------------------------------------------------
        #             Generación de los elementos de la ventana
        #region-----------------------------------------------------------------
                 
        #sizer general de la ventana
        SizerGeneral = wx.BoxSizer(wx.HORIZONTAL)

        #generación de la tabla de datos
        self.tabla = Grid_opt(self.pnl)
        self.tablaNR = 10
        self.tabla.CreateGrid(self.tablaNR,4)
        self.tabla.SetColSize(0, 65)
        self.tabla.SetColSize(1, 65)
        self.tabla.SetColSize(2, 65)
        self.tabla.SetColSize(3, 65)
        self.tabla.SetRowLabelSize(40)
        self.tabla.SetColLabelValue(0, 'x')
        self.tabla.SetColLabelValue(1, 'µx')
        self.tabla.SetColLabelValue(2, 'y')
        self.tabla.SetColLabelValue(3, 'µy')
        self.tabla.SetGridLineColour((200, 200, 200))
        self.tabla.DisableDragGridSize()
        self.tabla.DisableDragColSize()
        self.tabla.DisableDragRowSize()

        #generación de la ventana de resultados
        pnlResultados = wx.StaticBox(self.pnl, label="Resultados")
        pnlResultados.SetForegroundColour(wx.WHITE)
        pnlResultados_sizer=wx.StaticBoxSizer(pnlResultados, wx.HORIZONTAL)

        #generamos la ventana de resultados
        self.ResText = wx.TextCtrl(pnlResultados, value='Sin resultados todavía', 
                                   style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL, size=(290,120))

        #añadimos la ventana al sizer de resultados
        pnlResultados_sizer.Add(self.ResText, flag=wx.ALL, border=5)

        #generamos el panel de configuración
        pnlAjuste = wx.StaticBox(self.pnl, label="Configuración")
        pnlAjuste.SetForegroundColour(wx.WHITE)
        pnlAjuste_sizer = wx.StaticBoxSizer(pnlAjuste, wx.HORIZONTAL)

        #generamos los elementos dentro del panel de configuración
        TextFilas = wx.StaticText(pnlAjuste, label='# Filas')
        TextFilas.SetForegroundColour(wx.WHITE)
        self.IntFilas = wx.SpinCtrl(pnlAjuste, style= wx.SP_ARROW_KEYS|wx.TE_PROCESS_ENTER|wx.ALIGN_CENTER_HORIZONTAL,
                                min=1, max= 300, initial=10)
        BotonPlot = wx.Button(pnlAjuste,self.ID_PLOT, label='Graficar' )
        TextGrado = wx.StaticText(pnlAjuste, label='Grado del Polinomio')
        TextGrado.SetForegroundColour(wx.WHITE)
        self.IntGrado = wx.SpinCtrl(pnlAjuste, wx.SP_ARROW_KEYS|wx.ALIGN_CENTER_HORIZONTAL,
                                min=1, max=3, initial=1)
        BotonFit = wx.Button(pnlAjuste,self.ID_FIT, label='Ajustar' )

        #ajustamos todo dentro del panel de configuración
        pnlAjuste_sizer.Add(TextFilas, flag=wx.ALL|wx.CENTRE, border=5)
        pnlAjuste_sizer.Add(self.IntFilas, flag=wx.ALL|wx.CENTRE, border=5)
        pnlAjuste_sizer.Add(BotonPlot, flag=wx.ALL|wx.CENTRE, border=5)
        #pnlAjuste_sizer.Add(40, 20)
        pnlAjuste_sizer.Add(TextGrado, flag=wx.ALL|wx.CENTRE, border=5)
        pnlAjuste_sizer.Add(self.IntGrado, flag=wx.ALL|wx.CENTRE, border=5)
        pnlAjuste_sizer.Add(BotonFit, flag=wx.ALL|wx.CENTRE, border=5)

        #todo se montan algunos elementos sobre la ventana
        SizerIzq = wx.BoxSizer(wx.VERTICAL)
        SizerIzq.Add(self.tabla, wx.ALL|wx.ALIGN_TOP, border=5)
        SizerIzq.Add(pnlResultados_sizer, flag=wx.ALL, border=5)

        self.SizerSecundario = wx.BoxSizer(wx.VERTICAL)
        self.SizerSecundario.Add(pnlAjuste_sizer, wx.EXPAND)

        #generamos una grafica dummy por ahora
        self.midPan = wx.StaticBitmap(self.pnl)
        self.midPan.SetBitmap(wx.Bitmap(resource_path('odr_app_INTRO.png')))
        
        self.SizerSecundario.Add(self.midPan, flag=wx.ALL|wx.CENTRE, border=5)
            
        SizerGeneral.Add(SizerIzq, 1, wx.ALL, 10)
        SizerGeneral.Add(self.SizerSecundario,  2, wx.ALL, 10)
        self.pnl.SetSizer(SizerGeneral)
        self.pnl.Layout()
        #end region
#endregion 

        #-----------------------------------------------------------------------
        #             Binds de las acciones
        #region-----------------------------------------------------------------
        self.Bind(wx.EVT_MENU, self.OnQuit, QuitItem)
        self.Bind(wx.EVT_MENU, self.OnAbout, AboutItem)
        self.Bind(wx.EVT_SPINCTRL, self.OnCambiarFilas, self.IntFilas)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnCambiarFilas, self.IntFilas)
        self.Bind(wx.EVT_BUTTON, self.OnGraficar, BotonPlot)
        self.Bind(wx.EVT_BUTTON, self.OnAjustar, BotonFit)
        #endregion

    #---------------------------------------------------------------------------
    #             funciones de la aplicación
    #---------------------------------------------------------------------------
    def OnQuit(self, evt):
        #lo que pasa cuando apretamos cerrar
        self.Close()

    def OnAbout(self, evt):
        #lo que pasa cuando apretamos about
        wx.MessageBox("ODR App \nV 1.2 \n Contacto: edlope@fisica.unam.mx \n RLH - 08/09/2026",
                      "Acerca de...", wx.OK|wx.ICON_INFORMATION)
        
    def OnCambiarFilas(self, evt):
        #lo que pasa cuando cambiamos el número de filas
        FilasContador = self.IntFilas.GetValue()    
        if FilasContador > self.tablaNR:
            self.tabla.AppendRows(numRows=FilasContador-self.tablaNR)
        elif FilasContador < self.tablaNR:
            self.tabla.DeleteRows(numRows=self.tablaNR-FilasContador, pos=FilasContador)
        else:
            pass
        self.tablaNR = FilasContador
        self.pnl.Layout()
        
    def OnGraficar(self, evt):
        #lo que pasa cuando usamos el botón graficar
        
        #obtenemos la información que esté en la tabla
        try:
            data_x  = [float(self.tabla.GetCellValue(i,0)) for i in range(self.tablaNR)]
        except:
            wx.MessageBox('Hay datos faltantes o caracteres prohibidos en x', 
                          'Error en columna x', wx.OK|wx.ICON_ERROR)
            return
        
        try:
            data_dx  = [float(self.tabla.GetCellValue(i,1)) for i in range(self.tablaNR)]
        except:
            wx.MessageBox('Hay datos faltantes o caracteres prohibidos en µx', 
                          'Error en columna µ', wx.OK|wx.ICON_ERROR)
            return

        try:
            data_y  = [float(self.tabla.GetCellValue(i,2)) for i in range(self.tablaNR)]
        except:
            wx.MessageBox('Hay datos faltantes o caracteres prohibidos en y', 
                          'Error en columna y', wx.OK|wx.ICON_ERROR)
            return
        
        try:
            data_dy  = [float(self.tabla.GetCellValue(i,3)) for i in range(self.tablaNR)]
        except:
            wx.MessageBox('Hay datos faltantes o caracteres prohibidos en µ', 
                          'Error en columna µ', wx.OK|wx.ICON_ERROR)
            return

        #ahora borramos la gráfica que ya estaba
        self.SizerSecundario.Remove(1)
        self.midPan.Destroy()

        with graph_plt(self.pnl, data_x, data_dx, data_y, data_dy) as self.midPan:
            self.SizerSecundario.Add(self.midPan,flag=wx.ALL|wx.CENTRE, border=5)

        self.pnl.Layout()

    def OnAjustar(self,evt):
        #lo que pasa cuando apretamos ajustar
        
        #obtenemos la información que esté en la tabla
        try:
            data_x  = [float(self.tabla.GetCellValue(i,0)) for i in range(self.tablaNR)]
        except:
            wx.MessageBox('Hay datos faltantes o caracteres prohibidos en x', 
                          'Error en columna x', wx.OK|wx.ICON_ERROR)
            return
        
        try:
            data_dx  = [float(self.tabla.GetCellValue(i,1)) for i in range(self.tablaNR)]
        except:
            wx.MessageBox('Hay datos faltantes o caracteres prohibidos en µx', 
                          'Error en columna µ', wx.OK|wx.ICON_ERROR)
            return

        try:
            data_y  = [float(self.tabla.GetCellValue(i,2)) for i in range(self.tablaNR)]
        except:
            wx.MessageBox('Hay datos faltantes o caracteres prohibidos en y', 
                          'Error en columna y', wx.OK|wx.ICON_ERROR)
            return
        
        try:
            data_dy  = [float(self.tabla.GetCellValue(i,3)) for i in range(self.tablaNR)]
        except:
            wx.MessageBox('Hay datos faltantes o caracteres prohibidos en µ', 
                          'Error en columna µ', wx.OK|wx.ICON_ERROR)
            return
        
        #obtenemos el orden del polinomio que se piensa ajustar
        grado = self.IntGrado.GetValue()

        #generamos un ajuste básico para alimentar ODR
        seed_B = polyfit(data_x, data_y, grado, cov=False, w=None)
      
        #generamos el modelo para ODR
        modelo = polynomial(grado)

        #ahora se seleccionan los datos. ODR si introduce incertidumbre NO pesos, para esto se usa RealData 
        datos_odr = RealData(data_x, data_y, sx=data_dx, sy=data_dy) #las incertidumbre en x y en x son sx y sy

        #se carga el modelo y los datos
        odr_fit = ODR(datos_odr, modelo, beta0=seed_B[::-1]) #beta0 es la semilla, que se obtiene del ajuste anterior. 

        #se corre el modelo y los datos
        output = odr_fit.run()

        #creamos la salida de pprint, pero nosotros
        pp_out = self.out_print(grado, output.beta, output.sd_beta)

        #la ponemos donde debemos
        self.ResText.SetValue(pp_out)

        #ahora solo falta graficar, para ver que se hizo
        #ahora borramos la gráfica que ya estaba
        self.SizerSecundario.Remove(1)
        self.midPan.Destroy()

        with graph_fit(self.pnl, data_x, data_dx, data_y, data_dy, output, grado) as self.midPan:
            self.SizerSecundario.Add(self.midPan,flag=wx.ALL|wx.CENTRE, border=5)

        self.pnl.Layout()
        
    def out_print(self, n, beta, beta_err):
        # función que crea la salida del ajuste
        out = 'y='
        coef =[]
        xx = []


        for i in range(n+1):
            coef.append('a_%s' % i)
            xx.append('x^%s' % i)

        xx[0] = ''

        for i in range(n+1):
            out = out + ' %s%s ' % (coef[i],xx[i])
            if i < n:
                out = out + '+'
            else:
                out = out 

        mss = ''

        mss+= 'Modelo: ' + out 
        mss+= '\nParámetro 	Valor 	Incertidumbre' 

        for i in range(n+1):

            mss+= '\n%s	%.10f	%.10f' % (coef[i],beta[i],beta_err[i]) 

        return mss
            

#Rutina de inicio
if __name__ == '__main__':
    app =wx.App()
    win = ODR_app(None, style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.MINIMIZE_BOX)
    win.Show()
    app.MainLoop()
