import gtk
import parser
import gettext

_ = gettext.gettext


class EditableTreeView(gtk.TreeView):
    leaving_model_events = (gtk.keysyms.Up, gtk.keysyms.Down,
            gtk.keysyms.Return)
    leaving_events = leaving_model_events + (gtk.keysyms.Tab,
            gtk.keysyms.ISO_Left_Tab, gtk.keysyms.KP_Enter)

    def __init__(self, position):
        super(EditableTreeView, self).__init__()
        self.editable = position
        self.cells = {}

    def on_quit_cell(self, current_model, fieldname, value):
        modelfield = current_model[fieldname]
        if hasattr(modelfield, 'editabletree_entry'):
            del modelfield.editabletree_entry
        cell = self.cells[fieldname]

        # The value has not changed ... do nothing.
        if value == cell.get_textual_value(current_model):
            return

        try:
            real_value = cell.value_from_text(current_model, value)
            modelfield.set_client(current_model, real_value)
        except parser.UnsettableColumn:
            return

    def on_open_remote(self, current_model, fieldname, create, value):
        modelfield = current_model[fieldname]
        cell = self.cells[fieldname]
        if value != cell.get_textual_value(current_model) or not value:
            changed = True
        else:
            changed = False
        try:
            valid, value = cell.open_remote(current_model, create,
                    changed, value)
            if valid:
                modelfield.set_client(current_model, value)
        except NotImplementedError:
            pass
        return cell.get_textual_value(current_model)

    def on_create_line(self):
        model = self.get_model()
        if self.editable == 'top':
            method = model.prepend
        else:
            method = model.append
        ctx = self.screen.context.copy()
        if self.screen.current_model.parent:
            ctx.update(self.screen.current_model.parent.expr_eval(
                self.screen.default_get))
        new_model = model.model_group.model_new(domain=self.screen.domain,
                context=ctx)
        res = method(new_model)
        return res

    def __next_column(self, col):
        cols = self.get_columns()
        current = cols.index(col)
        for i in range(len(cols)):
            idx = (current + i + 1) % len(cols)
            renderer = cols[idx].get_cell_renderers()[0]
            if isinstance(renderer, gtk.CellRendererToggle):
                editable = renderer.get_property('activatable')
            else:
                editable = renderer.get_property('editable')
            if cols[idx].get_visible() and editable:
                break
        return cols[idx]

    def __prev_column(self, col):
        cols = self.get_columns()
        current = cols.index(col)
        for i in range(len(cols)):
            idx = (current - (i + 1)) % len(cols)
            renderer = cols[idx].get_cell_renderers()[0]
            if isinstance(renderer, gtk.CellRendererToggle):
                editable = renderer.get_property('activatable')
            else:
                editable = renderer.get_property('editable')
            if cols[idx].get_visible() and editable:
                break
        return cols[idx]

    def set_cursor(self, path, focus_column=None, start_editing=False):
        if focus_column and (focus_column._type in ('many2one','many2many')) \
                and self.screen.form:
            self.screen.form.message_state(_('Relation Field: F3: New F2: Open/Search'))
        elif focus_column and (focus_column._type in ('one2many')) \
                and self.screen.form:
            self.screen.form.message_state(_('Relation Field: F2: Open'))
        elif focus_column and (focus_column._type in ('boolean')):
            start_editing = False
        elif self.screen.form:
            self.screen.form.message_state('')
        return super(EditableTreeView, self).set_cursor(path, focus_column,
                start_editing)

    def set_value(self):
        path, column = self.get_cursor()
        store = self.get_model()
        if not path or not column:
            return True
        model = store.get_value(store.get_iter(path), 0)
        modelfield = model[column.name]
        if hasattr(modelfield, 'editabletree_entry'):
            entry = modelfield.editabletree_entry
            if isinstance(entry, gtk.Entry):
                txt = entry.get_text()
            else:
                txt = entry.get_active_text()
            self.on_quit_cell(model, column.name, txt)
        return True

    def on_keypressed(self, entry, event):
        path, column = self.get_cursor()
        store = self.get_model()
        model = store.get_value(store.get_iter(path), 0)

        if event.keyval in self.leaving_events:
            shift_pressed = bool(gtk.gdk.SHIFT_MASK & event.state)
            if isinstance(entry, gtk.Entry):
                txt = entry.get_text()
            elif isinstance(entry, gtk.ComboBoxEntry) \
                    and shift_pressed \
                    and event.keyval != gtk.keysyms.ISO_Left_Tab:
                model = entry.get_property('model')
                txt = entry.get_active_text()
                idx = 0
                for idx, line in enumerate(model):
                    if line[1] == txt:
                        break
                if event.keyval == gtk.keysyms.Up:
                    entry.set_active((idx - 1) % 3)
                elif event.keyval == gtk.keysyms.Down:
                    entry.set_active((idx + 1) % 3)
                return True
            else:
                txt = entry.get_active_text()
            entry.disconnect(entry.editing_done_id)
            self.on_quit_cell(model, column.name, txt)
            entry.editing_done_id = entry.connect('editing_done',
                    self.on_editing_done)
        if event.keyval in self.leaving_model_events:
            if self.screen.tree_saves:
                if not model.validate():
                    invalid_fields = model.invalid_fields
                    col = None
                    for col in self.get_columns():
                        if col.name in invalid_fields:
                            break
                    self.set_cursor(path, col, True)
                    self.screen.form.message_state(
                            _('Warning; field "%s" is required !') % \
                                    invalid_fields[col.name])
                    return True
                obj_id = model.save()
                if not obj_id:
                    return True
        if event.keyval in (gtk.keysyms.Tab, gtk.keysyms.KP_Enter):
            new_col = self.__next_column(column)
            self.set_cursor(path, new_col, True)
        elif event.keyval == gtk.keysyms.ISO_Left_Tab:
            new_col = self.__prev_column(column)
            self.set_cursor(path, new_col, True)
        elif event.keyval == gtk.keysyms.Up:
            self._key_up(path, store, column)
        elif event.keyval == gtk.keysyms.Down:
            self._key_down(path, store, column)
        elif event.keyval in (gtk.keysyms.Return,):
            if self.editable == 'top':
                new_path = self._key_up(path, store, column)
            else:
                new_path = self._key_down(path, store, column)
            col = None
            for column in self.get_columns():
                renderer = column.get_cell_renderers()[0]
                if isinstance(renderer, gtk.CellRendererToggle):
                    editable = renderer.get_property('activatable')
                else:
                    editable = renderer.get_property('editable')
                if column.get_visible() and editable:
                    col = column
                    break
            self.set_cursor(new_path, col, True)
        elif event.keyval == gtk.keysyms.Escape:
            if model.id is None:
                store.remove(store.get_iter(path))
                self.screen.current_model = False
            if not path[0]:
                self.screen.current_model = False
            if path[0] == len(self.screen.models.models) \
                    and path[0]:
                path = (path[0] - 1,)
            self.screen.display()
            self.set_cursor(path, column, False)
        elif event.keyval in (gtk.keysyms.F3, gtk.keysyms.F2):
            if isinstance(entry, gtk.Entry):
                value = entry.get_text()
            else:
                value = entry.get_active_text()
            entry.disconnect(entry.editing_done_id)
            newval = self.on_open_remote(model, column.name,
                                create=(event.keyval==gtk.keysyms.F3),
                                value=value)
            if isinstance(entry, gtk.Entry):
                entry.set_text(newval)
            else:
                entry.set_active_text(value)
            entry.editing_done_id = entry.connect('editing_done',
                    self.on_editing_done)
            self.set_cursor(path, column, True)
        else:
            modelfield = model[column.name]
            if isinstance(entry, gtk.Entry):
                entry.set_max_length(int(modelfield.attrs.get('size', 0)))
            # store in the model the entry widget to get the value in set_value
            modelfield.editabletree_entry = entry
            model.modified = True
            model.modified_fields.setdefault(column.name)
            return False

        return True

    def _key_down(self, path, store, column):
        if path[0] == len(store) - 1 and self.editable == 'bottom':
            self.on_create_line()
        new_path = (path[0] + 1) % len(store)
        self.set_cursor(new_path, column, True)
        self.scroll_to_cell(new_path)
        return new_path

    def _key_up(self, path, store, column):
        if path[0] == 0 and self.editable == 'top':
            self.on_create_line()
            new_path = 0
        else:
            new_path = (path[0] - 1) % len(store)
        self.set_cursor(new_path, column, True)
        self.scroll_to_cell(new_path)
        return new_path

    def on_editing_done(self, entry):
        path, column = self.get_cursor()
        if not path:
            return True
        store = self.get_model()
        model = store.get_value(store.get_iter(path), 0)
        if isinstance(entry, gtk.Entry):
            self.on_quit_cell(model, column.name, entry.get_text())
        elif isinstance(entry, gtk.ComboBoxEntry):
            self.on_quit_cell(model, column.name, entry.get_active_text())
