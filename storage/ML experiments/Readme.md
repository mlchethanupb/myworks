This folder contains ML analysis experimental data and codes, conducted in several steps. 

`behavior.py` plots how the storage behavior of individual VNfs changes over time.

 `CI.py` calculates and plots 95% confidence intervals of VNF's storage consumption for multiple independent test runs. 

Which metric/combinations of metrics and which regression technique suits better with the storage consumption of VNFs can be found out with `MulSVr.py`, `mulPolynomial.py` and `multipleLinear.py`. Also, it is possible to determine how accurately the *key metrics*, `VNF Runtime` and `Ingestion Rate` can predict other *predictor metrics* when predicting storage demand. 

`validation.py` performs 5 fold cross validation of SVR model over a range of hyper-parameters (gamma, C and epsilon) and returns the best model and the hyper-parameters given a set of predictor and outcome variables.

`sub-model.py` then creates the necessary sub-models using the cross validated hyper-parameters. 

`model-eval.py` creates comparison plots of different storage allocator models in terms of **Used**, **Allocated** and **Predicted** storage. 

`error.py` calculates RMSE and R<sup>2</sup> error between used and predicted disk usage.

`CI_prediction.py` plots confidence intervals of predicted disk usage for multiple test runs of the best model.
