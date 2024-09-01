from flet import (
    Container,
    ListView,
)
from typing import Optional, Callable

class SelectableListItem(Container):
    def __init__(
        self, 
        on_selected: Optional[Callable] = None,
        on_unselected: Optional[Callable] = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.on_selected = on_selected
        self.on_unselected = on_unselected
        
        self._ref_selectable_list: SelectableList
        self._is_selected = None
        
    @property
    def on_click(self):
        return super().on_click
    
    @on_click.setter
    def on_click(self, value):
        def wrapped_on_click(*args, **kwargs):
            self._list_item_on_click()
            if value is not None:
                value(*args, **kwargs)
        Container.on_click.__set__(self, wrapped_on_click)
    
    @property
    def is_selected(self) -> bool:
        return self._is_selected
    
    @property
    def _is_selected(self):
        return self.__is_selected
    
    @_is_selected.setter
    def _is_selected(self, value):
        if value == True:
            if self._on_selected is not None:
                self._on_selected(self)
        elif value == False:
            if self._on_unselected is not None:
                self._on_unselected(self)
        self.__is_selected = value
        
    def _list_item_on_click(self):
        self._ref_selectable_list._list_item_on_change(self)
    
    @property
    def on_selected(self):
        return self._on_selected
    @on_selected.setter
    def on_selected(self, value):
        self._on_selected = value
        
    @property
    def on_unselected(self):
        return self._on_unselected
    @on_unselected.setter
    def on_unselected(self, value):
        self._on_unselected = value
        
    
class SelectableList(ListView):
    def __init__(
        self, 
        selected_index: Optional[int] = None, 
        on_change: Optional[Callable] = None, 
        *args, 
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.on_change = on_change
        self._ref_selectable_list_item: SelectableListItem | None = None
        self.selected_index = selected_index
    
    @property
    def on_change(self):
        return self._on_change
    @on_change.setter
    def on_change(self, value):
        self._on_change = value
        
    @property
    def selected_index(self):
        return self._selected_index
    @selected_index.setter
    def selected_index(self, index: int | None):
        if index is None:
            ref_list_item = None
        else:
            control = self.controls[index]
            if isinstance(control, SelectableListItem):
                ref_list_item = control
            else:
                raise ValueError(f"selected_index must be an int or None. value: {type(index)}")
        self._list_item_on_change(ref_list_item)
        
    @property
    def controls(self):
        return super().controls
    
    @controls.setter
    def controls(self, value):
        if value is None:
            value = []
        if isinstance(value, list):
            ListView.controls.__set__(self, value)
        else:
            raise TypeError(f"controls must be a list or None. value: {type(value)}")

    def _list_update(self):
        for control in self.controls:
            if isinstance(control, SelectableListItem):
                control._ref_selectable_list = self

    def before_update(self):
        super().before_update()
        self._list_update()
    
    def _list_item_on_change(self, ref_selectable_list_item: SelectableListItem | None):
        if ref_selectable_list_item is self._ref_selectable_list_item:
            return
        if ref_selectable_list_item is None:
            if self._ref_selectable_list_item is not None:
                self._ref_selectable_list_item._is_selected = False
            self._ref_selectable_list_item = None
            self._selected_index = None
        else:
            for i, control in enumerate(self.controls):
                if control is ref_selectable_list_item:
                    if self._ref_selectable_list_item is not None:
                        self._ref_selectable_list_item._is_selected = False
                    self._ref_selectable_list_item = control  # type: ignore
                    self._ref_selectable_list_item._is_selected = True  # type: ignore
                    self._selected_index = i
                    break

        if self.on_change is not None:
            e = {
                "index": self._selected_index,
                "ref_list_item": self._ref_selectable_list_item
            }
            self.on_change(e)
