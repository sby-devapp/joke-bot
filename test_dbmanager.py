from app.db.db_manager import DBManager
from app.db.entities.joke import Joke

"""
My idea here in this test, I want to insert a tag in tags(id, name, created_by) table,
the record doesn't have an id, but after inserting I want to retrieve the id of that record.
"""
if __name__ == "__main__":
    db = DBManager()
    joke = Joke()
    joke.add_by = 6038394083
    joke.content = "testing joke insertion  ... "
    joke.language_code = "en"
    joke.status = "draft"

    joke.save()
    print(f"joke saved with id: {joke.id}")

    joke.delete()
    print("Joke deleted !")
