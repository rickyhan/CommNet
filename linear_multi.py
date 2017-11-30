"""
Using nn.Embedding as LookupTable
"""

from torch import nn
from torch.autograd import Variable
import torch

class LinearMulti(nn.Module):
    """
    Fetch the weight and bias from a lookup table based on agent/model id
    Params:
        sz_in: input layer
        sz_out: output layer
        model_ids: agent/model id
    Returns:
        Tensor [len(model_ids), sz_out]
    """
    def __init__(self, nmodels, sz_in, sz_out):
        super(LinearMulti, self).__init__()
        self.nmodels = nmodels
        self.sz_in = sz_in
        self.sz_out = sz_out

        if nmodels == 1:
            self.linear = nn.Linear(sz_in, sz_out)
        else:
            # XXX: potential bug - updateGradInput is overidden,
            # possible use of `register_backward_hook`
            self.weight_lut = nn.Embedding(nmodels, sz_in * sz_out) # 1x3x200
            self.bias_lut = nn.Embedding(nmodels, sz_out) # 1x3x20

    def forward(self, input, model_ids):
        """
        Params:
            input: shape [len(model_ids), sz_in]
        """
        if self.nmodels == 1:
            return self.linear(input)
        else:
            weight = self.weight_lut(model_ids) # 1 x 3 x 200
            weight_view = weight.view(-1, self.sz_in, self.sz_out) # 3 x 10 x 20
            bias = self.bias_lut(model_ids) # 1 x 3 x 20
            bias_view = bias.view(-1, self.sz_out) # 3x20

            a, b = input.size()
            input = input.view(a, 1, b) # 3x1x10

            out = torch.matmul(input, weight_view) # 3x1x20

            a, b, c = out.size()
            out = out.view(a, c) #3x20
            out = out.add(bias_view) # 3x20
            return out


if __name__ == "__main__":
    x = Variable(torch.ones(3, 4))
    model_ids = Variable(torch.LongTensor([[1, 2, 1]]))

    model = LinearMulti(3, 4, 1)
    y = model.forward(x, model_ids)
    target = Variable(torch.FloatTensor([[3], [10], [3]]))
    print(target)
    print(y)

    learning_rate = 1e-1
    optimizer = torch.optim.Adagrad(model.parameters(), lr=learning_rate)
    loss_fn = torch.nn.MSELoss(size_average=False)

    for i in range(100):
        optimizer.zero_grad()
        y = model(x, model_ids)
        loss = loss_fn(y, target)
        loss.backward(retain_graph=True)
        optimizer.step()
        print(model.weight_lut.weight)

    # # Note: in the original test, the weight of l1, l2 is copied to the
    # # weight of linear_multi. Then test the matmul results are the same
