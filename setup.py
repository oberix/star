from distutils.core import setup


setup(name='Star',
      version='0.2.2',
      description='Servabit daTa Analisys and Reporting',
      author='Marco Pattaro',
      author_email='marco.pattaro@servabit.it',
      packages=['star', 'star.remida', 'star.remida.plotters', 'star.share', 'star.sda', 'star.etl'],
      data_files=[],
      requires=['pandas (>=0.7.3)']
)
