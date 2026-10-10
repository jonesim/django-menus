import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="django-advanced-menus",
    version="1.0.2",
    author="Ian Jones",
    maintainer="Thomas Turner",
    description="Django app to render menus and load tabs with Ajax",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/django-advance-utils/django-advanced-menus",
    project_urls={"Upstream": "https://github.com/jonesim/django-menus"},
    include_package_data = True,
    packages=['django_menus'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=['ajax-advanced-helpers>=1.0.1'],
)
