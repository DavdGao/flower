import warnings
from collections import OrderedDict

import flwr as fl
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision.datasets import CIFAR10
from torchvision.transforms import Compose, Normalize, ToTensor
from tqdm import tqdm


# #############################################################################
# 1. Regular PyTorch pipeline: nn.Module, train, test, and DataLoader
# #############################################################################

warnings.filterwarnings("ignore", category=UserWarning)
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


class Net(nn.Module):
    """Model (simple CNN adapted from 'PyTorch: A 60 Minute Blitz')"""

    def __init__(self) -> None:
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, 5, padding=2)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(32, 64, 5, padding=2)
        self.fc1 = nn.Linear((28//2//2) * (28//2//2)*64, 1024)
        self.fc2 = nn.Linear(1024, 62)
        # self.fc3 = nn.Linear(84, 10)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(-1, (28//2//2) * (28//2//2)*64)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)


def train(net, trainloader, epochs):
    """Train the model on the training set."""
    print("Skip local training!")
    pass
    # criterion = torch.nn.CrossEntropyLoss()
    # optimizer = torch.optim.SGD(net.parameters(), lr=0.001, momentum=0.9)
    # for _ in range(epochs):
    #     for images, labels in tqdm(trainloader):
    #         optimizer.zero_grad()
    #         criterion(net(images.to(DEVICE)), labels.to(DEVICE)).backward()
    #         optimizer.step()


def test(net, testloader):
    """Validate the model on the test set."""
    print("Skip local evaluation!")
    return 0., 0.
    # criterion = torch.nn.CrossEntropyLoss()
    # correct, loss = 0, 0.0
    # with torch.no_grad():
    #     for images, labels in tqdm(testloader):
    #         outputs = net(images.to(DEVICE))
    #         labels = labels.to(DEVICE)
    #         loss += criterion(outputs, labels).item()
    #         correct += (torch.max(outputs.data, 1)[1] == labels).sum().item()
    # accuracy = correct / len(testloader.dataset)
    # return loss, accuracy


def load_data():
    """Load CIFAR-10 (training and test set)."""
    # trf = Compose([ToTensor(), Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])
    # trainset = CIFAR10("./data", train=True, download=True, transform=trf)
    # testset = CIFAR10("./data", train=False, download=True, transform=trf)
    # return DataLoader(trainset, batch_size=32, shuffle=True), DataLoader(testset)
    return None, None


# #############################################################################
# 2. Federation of the pipeline with Flower
# #############################################################################
net = Net().to(DEVICE)
trainloader, testloader = load_data()

# Define Flower client
class FlowerClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        return [val.cpu().numpy() for _, val in net.state_dict().items()]

    def set_parameters(self, parameters):
        params_dict = zip(net.state_dict().keys(), parameters)
        state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
        net.load_state_dict(state_dict, strict=True)

    def fit(self, parameters, config):
        self.set_parameters(parameters)
        train(net, trainloader, epochs=1)
        return self.get_parameters(config={}), 20, {}

    def evaluate(self, parameters, config):
        self.set_parameters(parameters)
        loss, accuracy = test(net, testloader)
        return loss, 20, {"accuracy": accuracy}


# from multiprocessing import Process
#
#
# class ClientManager(Process):
#     def __init__(self, n_client):
#         super().__init__()
#         self.n_client = n_client
#
#     def run(self) -> None:
#
#         fl.client.start_numpy_client(
#             server_address="127.0.0.1:8080",
#             client=FlowerClient(),
#         )


if __name__ == '__main__':
    # Start Flower client
    fl.client.start_numpy_client(
        server_address="172.24.224.187:8080",
        client=FlowerClient(),
    )
