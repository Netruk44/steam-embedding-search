
# Prepare machine for running model (run during docker build)

#from instructor_model import InstructorModel
from config import instructor_model_name
import sys
import os
#from InstructorEmbedding import INSTRUCTOR
from sentence_transformers.util import snapshot_download
from sentence_transformers import __version__ as sentence_transformers_version


# Load instructor model
#instructor = InstructorModel(
#    model_name = instructor_model_name,
#)

cache_folder = os.getenv('SENTENCE_TRANSFORMERS_HOME')
if cache_folder is None:
    try:
        from torch.hub import _get_torch_home

        torch_cache_home = _get_torch_home()
    except ImportError:
        torch_cache_home = os.path.expanduser(os.getenv('TORCH_HOME', os.path.join(os.getenv('XDG_CACHE_HOME', '~/.cache'), 'torch')))

    cache_folder = os.path.join(torch_cache_home, 'sentence_transformers')


# Download from hub with caching
snapshot_download(instructor_model_name,
                    cache_dir=cache_folder,
                    library_name='sentence-transformers',
                    library_version=sentence_transformers_version,
                    ignore_files=['flax_model.msgpack', 'rust_model.ot', 'tf_model.h5'],
                    use_auth_token=None)


sys.exit(0)