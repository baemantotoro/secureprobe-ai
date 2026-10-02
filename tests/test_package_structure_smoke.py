import secureprobe
import secureprobe.agent
import secureprobe.core
import secureprobe.models
import secureprobe.report
import secureprobe.source
import secureprobe.source.tools
import secureprobe.web
import secureprobe.web.tools
from secureprobe.main import main


def test_package_imports():
    assert secureprobe.__name__ == "secureprobe"
    assert secureprobe.agent.__name__ == "secureprobe.agent"
    assert secureprobe.core.__name__ == "secureprobe.core"
    assert secureprobe.models.__name__ == "secureprobe.models"
    assert secureprobe.report.__name__ == "secureprobe.report"
    assert secureprobe.source.__name__ == "secureprobe.source"
    assert secureprobe.source.tools.__name__ == "secureprobe.source.tools"
    assert secureprobe.web.__name__ == "secureprobe.web"
    assert secureprobe.web.tools.__name__ == "secureprobe.web.tools"


def test_main_entrypoint_runs():
    main()
