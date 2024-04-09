"""
Handling installation of external python packages inside of Blender's bundled python.
"""
import subprocess
import sys
import logging
from importlib.metadata import version as get_version, PackageNotFoundError
import bpy
from pathlib import Path

ADDON_NAME = __package__.split(".")[0]

PYPI_MIRROR = {
    # the original.
    'Default': '',
    # two mirrors in China Mainland to help those poor victims under GFW.
    'BFSU (Beijing)': 'https://mirrors.bfsu.edu.cn/pypi/web/simple',
    'TUNA (Beijing)': 'https://pypi.tuna.tsinghua.edu.cn/simple',
    # append more if necessary.
}


class InstallationError(Exception):
    """
    Exception raised when there is an error installing a package.

    Attributes
    ----------
    package_name : str
        The name of the package that failed to install.
    error_message : str
        The error message returned by pip.

    """

    def __init__(self, package_name, error_message):
        self.package_name = package_name
        self.error_message = error_message
        super().__init__(f"Failed to install {package_name}: {error_message}")


class PackageInstaller():
    def __init__(
        self,
        pypi_mirror_provider='Default',
        log_dir: str = None,
        requirements_dir: str = None
    ) -> None:
        self.pypi_mirror_provider = pypi_mirror_provider
        self.log_path: Path = Path(log_dir) if log_dir else \
            Path(Path.home(), '.externalpackage', 'logs')
        self.requirements_path: Path = Path(requirements_dir) if requirements_dir else \
            Path(__file__).parent

    def start_logging(self, logfile_name: str = 'side-packages-install') -> logging.Logger:
        """
        Configure and start logging to a file.

        Parameters
        ----------
        logfile_name : str, optional
            The name of the log file. Defaults to 'side-packages-install'.

        Returns
        -------
        logging.Logger
            A Logger object that can be used to write log messages.

        This function sets up a logging configuration with a specified log file name and logging level.
        The log file will be created in the `ADDON_DIR/logs` directory. If the directory
        does not exist, it will be created. The function returns a Logger object that can be used to
        write log messages.

        """
        # Create the logs directory if it doesn't exist
        self.log_path.mkdir(parents=True, exist_ok=True)

        # Set up logging configuration
        logfile_path = Path(self.log_path, f"{logfile_name}.log")
        logging.basicConfig(filename=logfile_path, level=logging.INFO)

        # Return logger object
        return logging.getLogger()

    @property
    def pypi_mirror_url(self) -> str:
        """
        Process a PyPI mirror provider and return the corresponding URL.

        Parameters
        ----------
        pypi_mirror_provider : str
            The PyPI mirror provider to process.

        Returns
        -------
        str
            The URL of the PyPI mirror.

        Raises
        ------
        ValueError
            If the provided PyPI mirror provider is invalid.

        """
        if self.pypi_mirror_provider.startswith('https:'):
            return self.pypi_mirror_provider
        elif self.pypi_mirror_provider in PYPI_MIRROR.keys():
            return PYPI_MIRROR[self.pypi_mirror_provider]
        else:
            raise ValueError(
                f"Invalid PyPI mirror provider: {self.pypi_mirror_provider}")

    @property
    def packages(self) -> dict:
        """
        Read a requirements file and extract package information into a dictionary.

        Parameters
        ----------
        requirements : str, optional
            The path to the requirements file. If not provided, the function looks for a `requirements.txt`
            file in the same directory as the script.

        Returns
        -------
        dict
            A dictionary containing package information. Each element of the dictionary is a dictionary containing the package name, version, and description.

        Example
        -------
        Given the following requirements file:
        ```python
        Flask==1.1.2 # A micro web framework for Python
        pandas==1.2.3 # A fast, powerful, flexible, and easy-to-use data analysis and manipulation tool
        numpy==1.20.1 # Fundamental package for scientific computing
        ```
        The function would return the following dictionary:
        ```python
        [
            {
                "package": "Flask",
                "version": "1.1.2",
                "description": "A micro web framework for Python"
            },
            {
                "package": "pandas",
                "version": "1.2.3",
                "description": "A fast, powerful, flexible, and easy-to-use data analysis and manipulation tool"
            },
            {
                "package": "numpy",
                "version": "1.20.1",
                "description": "Fundamental package for scientific computing"
            }
        ]
        ```
        """
        requirements_filepath = self.requirements_path / "requirements.txt"
        if requirements_filepath.is_file():
            with requirements_filepath.open('r') as f:
                lines = f.read().splitlines()
                packages = {}
                for line in lines:
                    try:
                        package, description = line.split('#')
                        package_meta = package.split('==')
                        name = package_meta[0].strip()
                        packages[name] = {
                            "name": name,
                            "version": package_meta[1].strip(),
                            "description": description.strip()
                        }
                    except ValueError:
                        # Skip line if it doesn't have the expected format
                        pass
            return packages
        else:
            raise FileNotFoundError(requirements_filepath)

    def is_installed(self, package_name: str) -> bool:
        """
        Check if the specified package is installed and the version matches that specified
        in the `requirements.txt` file.

        Parameters
        ----------
        package : str
            The name of the package to check.

        Returns
        -------
        bool
            True if the package is the current version, False otherwise.

        """
        package = self.packages.get(package_name)
        try:
            available_version = get_version(package['name'])
            return available_version == package['version']
        except PackageNotFoundError:
            return False

    def run_python(self, cmd_list: list = None, timeout: int = 600):
        """
        Runs pip command using the specified command list and returns the command output.

        Parameters
        ----------
        cmd_list : list, optional
            List of pip commands to be executed. Defaults to None.
        mirror_url : str, optional
            URL of a package repository mirror to be used for the command. Defaults to ''.
        timeout : int, optional
            Time in seconds to wait for the command to complete. Defaults to 600.

        Returns
        -------
        tuple
            A tuple containing the command list, command return code, command standard output,
            and command standard error.

        Example
        -------
        Install numpy using pip and print the command output
        ```python
        cmd_list = ["-m", "pip", "install", "numpy"]
        mirror_url = 'https://pypi.org/simple/'
        cmd_output = run_python(cmd_list, timeout=300)
        print(cmd_output)
        ```

        """

        # path to python.exe
        python_exe = Path(sys.executable).resolve()

        # build the command list
        cmd_list = [python_exe] + cmd_list

        # add mirror to the command list if it's valid
        if self.pypi_mirror_url and self.pypi_mirror_url.startswith('https'):
            cmd_list += ['-i', self.pypi_mirror_url]

        log = self.start_logging()
        log.info(f"Running Pip: '{cmd_list}'")

        # run the command and capture the output
        result = subprocess.run(cmd_list, timeout=timeout,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            log.error('Command failed: %s', cmd_list)
            log.error('stdout: %s', result.stdout.decode())
            log.error('stderr: %s', result.stderr.decode())
        else:
            log.info('Command succeeded: %s', cmd_list)
            log.info('stdout: %s', result.stdout.decode())
        # return the command list, return code, stdout, and stderr as a tuple
        return result

    def install_package(self, package: str) -> list:
        """
        Install a Python package and its dependencies using pip.

        Parameters
        ----------
        package : str
            The name of the package to install.
        pypi_mirror_provider : str, optional
            The name/url of the PyPI mirror provider to use. Default is 'Default'.

        Returns
        -------
        list
            A list of tuples containing the command list, return code, stdout, and stderr
            for each pip command run.

        Raises
        ------
        ValueError
            If the package name is not provided.

        Example
        -------
        To install the package 'requests' from the PyPI mirror 'MyMirror', use:
        ```
        install_package('requests', 'MyMirror')
        ```

        """
        if not package:
            raise ValueError("Package name must be provided.")

        print(f"Installing {package}...")
        print(f"Using PyPI mirror:\
            {self.pypi_mirror_provider} {self.pypi_mirror_url}")

        self.run_python(["-m", "ensurepip"]),
        self.run_python(["-m", "pip", "install", "--upgrade", "pip"])
        result = self.run_python(["-m", "pip", "install", package])

        return result

    def install_all_packages(self, pypi_mirror_provider: str = 'Default') -> list:
        """
        Install all packages listed in the 'requirements.txt' file.

        Parameters
        ----------
        pypi_mirror_provider : str, optional
            The PyPI mirror to use for package installation. Defaults to 'Default',
            which uses the official PyPI repository.

        Returns
        -------
        list
            A list of tuples containing the installation results for each package.

        Raises
        ------
        InstallationError
            If there is an error during package installation.

        Example
        -------
        To install all packages listed in the 'requirements.txt' file, run the following command:
        ```
        install_all_packages(pypi_mirror_provider='https://pypi.org/simple/')
        ```

        """
        results = []
        for package in self.packages.items():

            try:
                result = self.install_package(
                    package=f"{package.get('name')}=={package.get('version')}"
                )
                results.append(result)
            except InstallationError as e:
                raise InstallationError(
                    f"Error installing package {package.get('name')}: {str(e)}")
        return results


class EXTERNALPACKAGE_OT_Install_Package(bpy.types.Operator):
    bl_idname = 'externalpackage.install_package'
    bl_label = 'Install Given Python Package'
    bl_options = {'REGISTER', 'INTERNAL'}
    
    package: bpy.props.StringProperty(
        name='Python Package',
        description='Python Package to Install'
    )  # type: ignore
    version: bpy.props.StringProperty(
        name='Python Package',
        description='Python Package to Install'
    )  # type: ignore

    description: bpy.props.StringProperty(
        name='Operator description',
        default='Install specified python package.'
    )  # type: ignore

    @classmethod
    def description(cls, context, properties):
        return properties.description

    def execute(self, context):
        preferences = context.preferences.addons[ADDON_NAME].preferences
        installer = PackageInstaller(
            pypi_mirror_provider=preferences.pypi_mirror_provider,
            log_dir=preferences.log_dir,
            requirements_dir=preferences.requirements_dir
        )

        result = installer.install_package(f"{self.package}=={self.version}")
        if result.returncode == 0 and installer.is_installed(self.package):
            self.report(
                {'INFO'},
                f"Successfully installed {self.package} v{self.version}"
            )
        else:
            self.report(
                {'ERROR'},
                f"Error installing package. Please check the log files in \
                    '{preferences.log_dir}'."
            )
        return {'FINISHED'}
