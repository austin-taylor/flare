from collections import defaultdict, Counter
import random
from math import log
from itertools import repeat
import sys


class MarkovModel(object):
    """
    High-order Markov model of string sequences.

    Args:
        order (int): the desired order of the Markov model.
    Returns:
        an instance of MarkModel
    Example:
        m = MarkModel(4)
        m.load_from_file("shakespeare.txt")
        m.train()
        m.simulate(500)
        m.likelihood("valid words and phrases")
        m.likelihood("ddsm3902,/0(")
    """

    def __init__(self, order):
        self.order = order
        self.training_data = None
        self.trained = False
        self.histories = defaultdict(Counter)
        self.normed = defaultdict(Counter)
        self.prior = .001

    def load(self, s):
        """
        Load training data as a single long string.

        Args:
            s (str): a single string to use as training data
        Returns:
            None
        """
        self.training_data = "~" * self.order + s + "~" * self.order

    def load_from_file(self, file_path):
        """
        Load training data with path to text file.

        Args:
            file_path (str) : a file path
        Returns:
            None
        """
        with open(file_path, 'r') as in_file:
            s = in_file.read()
        self.training_data = "~" * self.order + s + "~" * self.order

    def train(self):
        """
        Crunch through the input data to compute Markov transition matrix.
        """
        if not self.training_data:
            raise ValueError(
                "Must load data before Markov model can be trained."
            )

        # update tranistion matrix counts for all relevant substrings
        for i in range(len(self.training_data) - self.order):
            substr = self.training_data[i: i + self.order]
            nxt = self.training_data[i + self.order]
            self.histories[substr][nxt] += 1

        # compute proper probability measure from transition counts
        self.normed = self.__normalize(self.histories)

        # update prior
        # prior is set to be two orders of magnitude smaller
        #   than the smallest observed transition probability
        probabilities = [[v for (k, v) in list(d.items())]
                         for d
                         in list(self.normed.values())]
        self.prior = .01 * min(
            [val for sublist in probabilities for val in sublist]
        )

        # update state
        self.trained = True

    def simulate(self, length):
        """
        Generate a new sequence drawn from the trained Markov model.

        Args:
            length (int): The length of the sequence to be produced
        Returns:
            (str): A simulated sequence of the proscribed length,
                     drawn from the tained Markov model
        """
        if not self.trained:
            raise ValueError(
                "Must train model first before simulating new sequences"
            )

        # begin with a random seed
        seed = random.choice(list(self.histories.keys()))
        result = ""

        # append one letter at a time, sampled from the transition matrix
        for i in range(length):
            distribution = self.normed[seed[- self.order:]]
            letter = self.__sample_letter(distribution)
            seed += letter
            result += letter
        return result

    def likelihood(self, token):
        """
        Compute the log likelihood of a test sequence
            given the trained Markov model.

        Args:
            token (str): A test sequence of interest
        Returns:
            (float): The computed average log likliehood of the test token.
        """
        if not self.trained:
            raise ValueError(
                "Must train model first before evaluating likelihood"
            )

        # lookup the probability of transitioning from subtr -> nxt
        # return prior if transition is yet unobserved
        def lookup(substr, nxt):
            try:
                dist = self.normed[substr]
                prob = dist[nxt]
                return prob if prob > 0.0 else self.prior
            except KeyError:
                return self.prior

        if len(token) < (self.order + 1):
            return log(self.prior)
        else:
            log_likelihoods = []

            # compute log likelihood for each transition in the test sequence
            for i in range(len(token) - self.order):
                substr, nxt = token[i: i + self.order], token[i + self.order]
                log_likelihoods.append(log(lookup(substr, nxt)))

            # return the average log likelihood per transition
            return 1 / float(len(log_likelihoods)) * sum(log_likelihoods)

    def __normalize(self, a):
        """
        Normalize the transition counts into a proper transition matrix.
        """
        output = defaultdict(repeat(defaultdict(float)).__next__)
        for (substr, dictionary) in list(a.items()):
            total = sum(dictionary.values())

            output[substr] = {key: dictionary[key] / float(total)
                              for key
                              in list(dictionary.keys())}
        return output

    def __sample_letter(self, distribution):
        """ Produce a random draw from a Categorical distribution.  """
        r = random.random()
        for (key, num) in list(distribution.items()):
            r -= num
            if r <= 0:
                return key

if __name__ == '__main__':
    file_path = sys.argv[1]
    m = MarkovModel(5)
    print("Loading text file. ")
    m.load_from_file(file_path)
    print("Training model. ")
    m.train()
    print(("A simulated sequence: %s" % m.simulate(500)))
