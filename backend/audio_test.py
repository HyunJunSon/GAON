import opensmile

smile = opensmile.Smile(
    feature_set=opensmile.FeatureSet.ComParE_2016,
    feature_level=opensmile.FeatureLevel.Functionals,
)
y = smile.process_file('./test_audio.webm')

mfcc = y[[c for c in y.index if "mfcc" in c]]
print(mfcc)
