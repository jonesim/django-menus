import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="django-tab-menus",
    version="0.0.11",
    author="Ian Jones",
    description="Django app to render menus and load tabs with Ajax",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jonesim/django-menus",
    include_package_data = True,
    packages=['django_menus'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=['django-ajax-helpers'],
)
