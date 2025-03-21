from setuptools import setup, find_packages

setup(
    name="shell_queue_manager",
    version="0.1.0",    
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    install_requires=[
        "flask>=2.0.0",
        "pydantic>=1.9.0",
        "pytest>=6.2.5",
    ],
    entry_points={
        "console_scripts": [
            "shell-queue=shell_queue_manager.__main__:main",
        ],
    },
    author="Yizhen Jia",
    author_email="yizhen.jia96@gmail.com",
    description="A shell script queue manager with REST API",
    keywords="shell, queue, script, api",
    python_requires=">=3.10",
)