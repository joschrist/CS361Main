from tracker import storage

VALID_TYPES = ("book", "movie", "game", "album")

class TrackerError(Exception):

    def __init__ (self, code, existing=None):
        super().__init__(code)
        self.code = code
        self.existing = existing

def add_item(title, type_, allow_duplicate=False, path=storage.DEFAULT_DB_PATH):
    title, type_ = _clean_fields(title, type_, required=True)

    if not allow_duplicate:
        existing = storage.find_duplicate(title, type_, path=path)
        if existing:
            raise TrackerError("duplicate", existing=existing)
    
    item_id = storage.insert_item(title, type_, path=path)
    return storage.get_item(item_id, path=path)

def get_item(item_id, path=storage.DEFAULT_DB_PATH):
    item = storage.get_item(item_id, path)
    if not item:
        raise TrackerError("not_found")
    return item

def list_items(path=storage.DEFAULT_DB_PATH):
    return storage.list_items(path)

def edit_item(item_id, title=None, type_=None, path=storage.DEFAULT_DB_PATH):
    if title is None and type_ is None:
        raise TrackerError("nothing_to_change")
    
    title, type_ = _clean_fields(title, type_)

    old = get_item(item_id, path=path)
    storage.update_item(item_id, title, type_, path)
    return old, get_item(item_id, path)

def delete_item(item_id, path=storage.DEFAULT_DB_PATH):
    old = get_item(item_id, path=path)
    storage.delete_item(item_id, path)
    return old

def _clean_fields(title=None, type_=None, required= False):

    if title is not None or required:
        title = (title or "").strip()
        if not title:
            raise TrackerError("blank_title")
        
    if type_ is not None or required:
        type_ = (type_ or "").strip().lower()
        if type_ not in VALID_TYPES:
            raise TrackerError("invalid_type")

    return title, type_