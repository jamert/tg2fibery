from setuptools import setup

setup(
    name="tg2fibery",
    version="22.1.dev",
    description="Digital thread to push data from Telegram to Fibery",
    author="Artem Daineko",
    author_email="dayneko.ab@gmail.com",
    py_modules=["rst2wiki"],
    # TODO: install_requires
    entry_points="""
        [console_scripts]
        tg2fibery = tg2fibery:main
    """,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
    ],
)
