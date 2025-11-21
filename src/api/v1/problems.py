from entity import Entity

class ProblemEntity(Entity):
    """Entity representing a problem."""

    def __init__(self):
        super().__init__(
            name="problem",
            collection_name="problems",
            dump_schema=None,
            orm_class=None,
            creation_schema=None,
            update_schema=None,
        )


    def get(self, problem_id: str) -> dict:
        """Retrieve a problem by its ID."""
        # Here we should implement backend logic to get the problem from the database.
        # For now, we return a placeholder.
        return {"id": problem_id, "title": "Sample Problem", "description": "This is a sample problem."}
    

PROBLEM = ProblemEntity()