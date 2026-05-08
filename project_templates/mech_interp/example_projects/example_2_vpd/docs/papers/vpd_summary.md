---
title: "Paper Summary: Interpreting Language Model Parameters"
authors:
  - name: Lucius Bushnaq
    affiliation: Goodfire
    core_contributor: true
    url: https://goodfire.ai
  - name: Dan Braun
    affiliation: Goodfire
    core_contributor: true
    equal_contribution: true
    url: https://goodfire.ai
  - name: Oliver Clive-Griffin
    affiliation: Goodfire
    equal_contribution: true
    core_contributor: true
    url: https://goodfire.ai
  - name: Bart Bussmann
    affiliation: MATS
    url: https://goodfire.ai
  - name: Nathan Hu
    affiliation: MATS
    url: https://goodfire.ai
  - name: Michael Ivanitskiy
    affiliation: MATS
    url: https://goodfire.ai
  - name: Linda Linsefors
    affiliation: Independent
  - name: Lee Sharkey
    affiliation: Goodfire
    core_contributor: true
    url: https://goodfire.ai
affiliation: Goodfire, MATS
correspondence: lee@goodfire.com
published: "May 5th 2026"
is_blog: false
---

Language models are some of the most remarkable computer programs in existence. They implement algorithms humans have tried and failed to write by hand for decades. Yet the "code" these algorithms are implemented by is "*neural* code", which is written, somehow, as enormous, inscrutable matrices of parameters.

As a result, the field of interpretability has focused mainly on trying to understand the models' activations — the models’ “thoughts”. But reading these thoughts doesn’t immediately explain the computations that gave rise to them. To understand them deeply, we should understand not just the inputs and outputs to their computations, but *the computations themselves*.

Ad**V**ersarial **P**arameter **D**ecomposition<footnote>Unfortunately, "APD" was taken by some of our previous work!</footnote> (VPD) is our technique for doing this in a language model. By splitting the model's parameters into simple, understandable pieces, we are able to directly study their structure and the algorithms they implement.

We used VPD to decompose the weight matrices in a 67M-parameter language model. Using this new view into the network's parameters, we can:

- **Identify algorithms implemented in attention layers**, even when they are distributed across attention heads<footnote>indeed we find that those algorithms are *usually* distributed across attention heads!</footnote>;
- **Edit the original model's behavior with no training** — performing "brain surgery" directly on the model's "neural code";
- **Recover small subnetworks** responsible for specific, abstract behaviors.

We think this is a meaningful step toward a more bottom-up form of interpretability: one that explains computation in the model’s own terms, rather than imposing our own abstractions, top-down.

## VPD, or, How to take apart a neural network

To understand a complex object, it helps to think of it in terms of simpler pieces: cars in terms of parts; bodies in terms of organs; chemicals in terms of atoms; computer programs in terms of functions. Unfortunately, language models seem messier. The obvious candidates for these pieces, such as attention heads or MLP neurons<footnote>Though note that in many cases, neurons can and do correspond to interpretable functional roles, e.g. Arora et al. (2025) and upcoming Goodfire work. We note that it nonetheless remains unlikely that interpretations of networks in terms of individual neurons are the most parsimonious interpretations.</footnote>, often do not cleanly correspond to interpretable functional roles. And other methods such as sparse autoencoders don’t provide a comprehensive solution here, since they decode the model’s activations—the inputs and outputs of computations on the dataset—not the model itself. If simple pieces do exist, they are somehow encoded into the model's millions to trillions of parameters. Our job, then, is to tease apart these pieces.

VPD is an unsupervised process for identifying these pieces using gradient descent. To do so, we need to imagine what properties these pieces would have, so that we can optimize for them.

Firstly, we'd like each one to be mechanistically simple, so that we can understand each in isolation and in combination with each other. To enforce this, we constrain each piece to be a simple (rank one) matrix. These matrices must sum together to recreate the model's original weights.

We'd also like each to perform a specific computational role. The weights of a model might encode that "Paris is the capital of France", or that "The sky is blue". But for prompts where this knowledge isn't needed, we should be able somehow to remove this knowledge from the parameters without hurting performance on those prompts. In other words, these subcomponents are not causally important on this prompt. Finding pieces with this property should be possible because language models contain a vast amount of unrelated complexity.

A good matrix subcomponent, then, is one which is needed only to fulfil a specific role, and can otherwise be removed (or not!) from the model's parameters without hurting performance.

To define when subcomponents are causally important, we train an auxiliary model, the causal importance network. On any given prompt, the causal importance network predicts the minimum number of subcomponents that are causally important to reproduce the model's behavior on that prompt. This means we’re training both the subcomponents (our actual decomposition) and a model that predicts their causal importances. Meanwhile, we take the subcomponents that the causal importance network has selected and train them to better replicate the model’s computations. Together, this gives us computationally simple reproductions of the model's computations.

Our decomposition should approximate the behaviour of the target network regardless of what we do with causally unimportant subcomponents. We therefore actively search for combinations that break the auxiliary model's prediction of which subcomponents are causally unimportant, which stress-tests both the subcomponents and the selection made by the causal importance model. This helps ensure that the subcomponents we've labelled as unimportant are truly irrelevant, and that the subcomponents we've kept are a sufficient explanation of the network's behaviour.

In summary, if we learn subcomponents that:

- sum exactly to the original network;
- are mechanistically simple;
- are causally important as rarely as possible;
- and still behave like the original model,

then, we can be confident that we've found real, computational structure.

So we applied our method to our language model and found parameter subcomponents with these properties. What did we find?

## Our Decomposed Language Model

After applying VPD, the obvious first question is whether the resulting parameter subcomponents are actually interpretable objects, since we would ultimately like to make sense of their computational roles. Indeed, we find that they often activate in coherent semantic or syntactic contexts. You can browse a selection below:

```components
data: data/model-overview
ci_only: true
caption: Browse all VPD parameter subcomponents by weight matrix. Green highlights indicate causal importances.
```

There are also relatively few subcomponents: Decomposing all 24 matrices in the network, we identify only ~10,000 subcomponents.

### Interpreting Attention Layers

Notably, VPD can decompose attention layers. Attention has been one of the most persistent bottlenecks in mechanistic interpretability, often necessitating “half solutions”, with none of the methods capable of automatically identifying attention computations that span multiple attention ‘heads’.

VPD works on attention natively, finding subcomponents in attention weights the same way it does in any other layer. In our model, this is enough to recover interpretable attention algorithms directly in weight space, including previous-token behavior and a syntax-boundary routing behavior. In both cases, we find a pair of query and key subcomponents, distributed across heads, which seem to interact to perform the specific functional role.

While this is exciting specifically for attention, the broader point is that **VPD can be arbitrarily applied to any neural network architecture**.

### Model Editing

If our parameter subcomponents have cleanly isolated the true mechanisms of the model, we should be able to use them to perform clean, targeted changes. We tried this and were able to make a precise and predictable change to the model's behaviour by directly editing the subcomponents, with no training required.

Specifically, we found a subcomponent responsible for recognising the eyes of emoticons such as `;)`, `:(`, or `=)`. We altered this subcomponent to directly output the model’s unembedding vector for `o`, producing a model which predicts all emoticons as shocked faces!

<figure class="fig-emojis">
<label id="fig:emojis"/>
<img src="figures/emojis.png">
</figure>

Despite being the first editing approach we tried, our edit has similarly low levels of “off-target” effects as (uninterpretable) fine-tuning methods (though there’s still a performance gap). Nevertheless, the ability to make precise edits like this demonstrates that VPD identifies real computational machinery within models. And it does so well enough that we can begin to control it directly.

### Describing Model Behaviours with Subnetworks

We can use VPD to study specific model behaviours in terms of the parameter subcomponents the model uses to perform them, and show how information flows between those subcomponents from input to output.

For a given next-token prediction, we can identify the necessary subcomponents and compute an attribution graph — a rough approximation of how strongly the subcomponents interact — to trace how the model computes the output.

```graph
id: princess-full
data: data/graphs/princess-full.json
details: data/graphs/princess-full-details.json
```

Above is one such graph, showing the set of subcomponents — the subnetwork — required to predict ` her` instead of ` his` in the prompt `the princess lost her crown`. If you look carefully, it is possible to find two logical, interpretable pathways: one that seems to route a 'femaleness' signal from ` princess` forward through attention, and one that detects the verb ` lost` and upweights object pronouns (including ‘her’). Combined, this leads to ‘her’ being the model’s prediction.

## Conclusion

Language models' parameters have widely been considered irreducibly, impenetrably complex. We now have mounting evidence that this is not the case; that there is interpretable structure that we can find and understand. We're excited to scale to larger models, while developing deeper understandings of parameter subcomponents and their interactions. It remains likely that the technique will require further iteration to achieve this. However, we think future versions will fundamentally resemble VPD.

Ultimately, we would like to understand neural networks well enough to be able to intentionally design them, so that they have more of the properties we want and fewer of those we do not. By enabling decomposition of networks’ parameters into mechanistically faithful, minimal, simple parts, we think VPD is an exciting step toward that vision.

