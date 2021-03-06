import datetime

import torch
from torch import nn, optim


class Bot:
    def __init__(self, num_states, num_actions, path=None):
        self.num_states = num_states
        self.num_actions = num_actions
        self.alpha = 0.0000001
        # self.eps = 0.00000001
        self.eps = 1 / num_states
        self.set_model(path)
        self.optimizer = optim.Adam(
            params=self.model.parameters(),
            lr=self.alpha,
            eps=self.eps,
        )
        self.memory = []

    def set_model(self, path):
        self.load_model(path)

    def calculate_returns(self, rewards):
        returns = torch.zeros(rewards.shape)
        g_t = 0
        for t in reversed(range(0, len(rewards))):
            g_t = g_t * .99 + rewards[t].item()
            returns[t] = g_t
        return returns.detach()

    def act(self, state):
        with torch.no_grad():
            state = torch.FloatTensor(state)
            probs = self.model(state)
            policy_probs = torch.distributions.Categorical(probs)
        return policy_probs.sample()

    def append_sample(self, state, action, reward):
        state = torch.FloatTensor(state)
        reward = torch.FloatTensor([reward])
        self.memory.append((state, action, reward))

    def update(self):
        states = torch.stack([m[0] for m in self.memory])
        actions = torch.stack([m[1] for m in self.memory])
        rewards = torch.stack([m[2] for m in self.memory])

        returns = self.calculate_returns(rewards)
        returns = (returns - returns.mean()) / returns.std()
        self.optimizer.zero_grad()
        policy_log_probs = self.model(torch.FloatTensor(states)).log()
        policy_loss = torch.cat([-lp[a].unsqueeze(0) * g for a, lp, g in zip(actions, policy_log_probs, returns)])
        policy_loss = policy_loss.sum()
        policy_loss.backward()

        self.optimizer.step()

        self.memory = []
        return policy_loss.item()

    def save_model(self, path):
        torch.save(self.model.state_dict(), path)

    def load_model(self, path=None):
        self.model = nn.Sequential(
            nn.Linear(self.num_states, 32),
            nn.ReLU(),
            nn.Linear(32, 32),
            nn.ReLU(),
            nn.Linear(32, self.num_actions),
            nn.Softmax(),
        )
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        print(device)
        self.model.to(device)
        if path:
            self.model.load_state_dict(torch.load(path))
            self.model.eval()
