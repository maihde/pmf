from core import *

class NotificationAdapter(object):
    """
    An adapter that binds a callback to
    object notifications. 
    """
    __slots__ = [
                 "callback",
                 "eventTypes",
                 "target",
                 "__target",
                ]

    def __init__(self, callback=None, eventTypes=Notification.EventTypes):
        self.callback = callback
        self.eventTypes = eventTypes
        self.__target = None

    def setTarget(self, target):
        self.__target = target

    def getTarget(self):
        return self.__target
    target = property(fset=setTarget, fget=getTarget)

    def notify(self, notification):
        if notification.eventType not in self.eventTypes:
            return # We aren't interested in this type of event
        self.callback(notification)




class AllContentNotificationAdapter(NotificationAdapter):
    """
    An adapter that binds a callback to
    object notifications for the object and
    all decendants of the object. 
    """
    def setTarget(self, target):
        if self.target != None:
            self.__recursiveRemoveAdapter(self.target)
        super(AllContentNotificationAdapter, self).setTarget(target)
        self.__recursiveAddAdapter(target)
    target = property(fset=setTarget, fget=NotificationAdapter.getTarget)

    def __recursiveAddAdapter(self, obj):
        if isinstance(obj, MObject):
            obj.mAddAdapter(self)
            for k in dir(obj):
                if k.startswith("_") or callable(k): continue
                attr = getattr(obj, k)
                self.__recursiveAddAdapter(attr)

    def __recursiveRemoveAdapter(self, obj):           
        if isinstance(obj, MObject):
            obj.mRemoveAdapter(self)
            for k in dir(obj):
                attr = getattr(obj, k)
                self.__recursiveRemoveAdapter(attr)

    def notify(self, notification):
        self.callback(notification)
        if notification.newValue != None:
            try:
                for nv in notification.newValue:  self.__recursiveAddAdapter(nv)
            except TypeError:
                self.__recursiveAddAdapter(notification.newValue)
        if notification.oldValue != None:
            try:
                for nv in notification.oldValue:  self.__recursiveRemoveAdapter(nv)
            except TypeError:
                self.__recursiveRemoveAdapter(notification.newValue)