# Set the CRAN mirror
options(repos = "https://cran.r-project.org/")

# Read the packages from packages.txt
packages <- readLines("rpackages.txt")

# Install each package into the project library
for (pkg in packages) {
    install.packages(pkg)
}
