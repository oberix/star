from distutils.core import setup


setup(name='Star',
      version='0.2.3',
      description='Servabit daTa Analisys and Reporting',
      author='Marco Pattaro',
      author_email='marco.pattaro@servabit.it',
      packages=['star', 'star.remida', 'star.remida.plotters', 'star.share'],
      data_files=[],
      scripts=["bin/remida"],
      requires=['pandas (>=0.7.3)']
)
