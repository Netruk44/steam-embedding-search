
# Prepare machine for running model (run during docker build)

from instructor_model import InstructorModel
from config import instructor_model_name
import sys

# Load instructor model
instructor = InstructorModel(
    model_name = instructor_model_name,
)

sys.exit(0)