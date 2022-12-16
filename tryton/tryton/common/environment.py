#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.


class EvalEnvironment(dict):

    def __init__(self, parent, check_load, eval_type='eval'):
        super(EvalEnvironment, self).__init__()
        self.parent = parent
        self.check_load = check_load
        assert eval_type in ('eval', 'on_change')
        self.eval_type = eval_type

    def __getitem__(self, item):
        if item == 'id':
            return self.parent.id
        if item == '_parent_' + self.parent.parent_name and self.parent.parent:
            return EvalEnvironment(self.parent.parent, self.check_load,
                eval_type=self.eval_type)
        if self.eval_type == 'eval':
            return self.parent.get_eval(check_load=self.check_load)[item]
        else:
            return self.parent.group.fields[item].get_on_change_value(self.parent,
                check_load=self.check_load)

    def __getattr__(self, item):
        return self.__getitem__(item)

    def get(self, item, default=None):
        try:
            return self.__getattr__(item)
        except Exception:
            pass
        return super(EvalEnvironment, self).get(item, default)

    def __nonzero__(self):
        return True

    def __str__(self):
        return str(self.parent)

    __repr__ = __str__

    def __contains__(self, item):
        if item == 'id':
            return True
        if item == '_parent_' + self.parent.parent_name and self.parent.parent:
            return True
        if self.eval_type == 'eval':
            return item in self.parent.get_eval(check_load=self.check_load)
        else:
            return item in self.parent.group.fields
