from setuptools import setup, find_packages

setup(
    name="watchtower-ai",
    version="0.1.0",
    description="Runtime intelligence for multi-agent AI teams",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[],  # No hard dependencies — works with whatever LangGraph version you have
    extras_require={
        "demo": ["langgraph", "langchain-core"],
    },
)
