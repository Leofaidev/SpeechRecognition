_PLATFORM = __name__.split(".")[1]  # "linux" or "macos"

def __getattr__(name):
    raise NotImplementedError(
        f"{name} is not implemented for platform '{_PLATFORM}'. "
        f"This stub exists to support future ports (see Spec Section 17)."
    )
