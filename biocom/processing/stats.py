"""Statistical utilities for outlier detection.

Provides robust statistical estimators and outlier probability calculations
for signal processing.
"""

import numpy as np
from scipy.stats import norm


def robust_std(x):
    """Estimate standard deviation from interquartile range.
    
    Uses the interquartile range to robustly estimate standard deviation,
    resistant to outliers.
    
    :param x: Data array
    :type x: ndarray
    :return: Estimated standard deviation
    :rtype: float
    """
    q1 = np.percentile(x, 25)
    q3 = np.percentile(x, 75)

    return (q3 - q1) / 1.349


def outlier_prob(x, mu_in, sigma_in, sigma_out, p_prior):
    """Estimate outlier probability using Bayesian inference.
    
    Uses a mixture model with inlier and outlier distributions to calculate
    the posterior probability that each point is an outlier.
    
    :param x: Data array
    :type x: ndarray
    :param mu_in: Mean of inlier distribution
    :type mu_in: ndarray or float
    :param sigma_in: Standard deviation of inlier distribution
    :type sigma_in: ndarray or float
    :param sigma_out: Standard deviation of outlier distribution
    :type sigma_out: ndarray or float
    :param p_prior: Prior probability of any point being an outlier
    :type p_prior: float
    :return: Posterior outlier probability for each point
    :rtype: ndarray
    """
    pdf_in = norm.pdf(x, mu_in, sigma_in)
    pdf_out = norm.pdf(x, mu_in, sigma_out)
    p_out = p_prior * pdf_out / ((1 - p_prior) * pdf_in + p_prior * pdf_out)
    dev = np.abs(x - mu_in)
    # Don't consider data points with smaller deviations than sigma_in to be outliers
    p_out[dev <= sigma_in] = 0
    return p_out