import csv

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torchvision.models as models
import torchvision.transforms as transforms
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from torch.utils.data import DataLoader, random_split
from torchvision.datasets import ImageFolder


class EnhancedLeNet(nn.Module):
    def __init__(self, num_classes=10):
        super(EnhancedLeNet, self).__init__()
        # First convolutional layer C1
        self.conv1 = nn.Conv2d(
            1, 32, kernel_size=5, padding=2
        )  # padding to keep size 28x28
        # First max-pooling layer P1
        self.pool1 = nn.MaxPool2d(
            kernel_size=2, stride=2
        )  # Resulting in 14x14 feature maps

        # Second convolutional layer C2
        self.conv2 = nn.Conv2d(
            32, 64, kernel_size=5, padding=2
        )  # padding to keep size 14x14
        # Second max-pooling layer P2
        self.pool2 = nn.MaxPool2d(
            kernel_size=2, stride=2
        )  # Resulting in 7x7 feature maps

        # Fully connected layers
        self.fc1 = nn.Linear(64 * 7 * 7, 1024)
        self.fc2 = nn.Linear(1024, num_classes)

        # Dropout layer
        self.dropout = nn.Dropout(0.5)

    def forward(self, x):
        # Convolutional and max pooling layers
        x = F.relu(self.conv1(x))
        x = self.pool1(x)
        x = F.relu(self.conv2(x))
        x = self.pool2(x)

        # Flatten the output for fully connected layers
        x = torch.flatten(x, 1)

        # Fully connected layers with dropout
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)

        # Softmax output layer
        return F.log_softmax(x, dim=1)


class BasicCNN(nn.Module):
    def __init__(self, num_classes=10):
        super(BasicCNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 16, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=1)
        self.fc1 = nn.Linear(
            32 * 7 * 7, 128
        )  # Adjust based on your input size after conv layers
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.max_pool2d(x, 2)
        x = F.relu(self.conv2(x))
        x = F.max_pool2d(x, 2)
        x = torch.flatten(x, 1)
        x = F.relu(self.fc1(x))
        return self.fc2(x)


class CustomVGG16(nn.Module):
    def __init__(self, num_classes=25):
        super(CustomVGG16, self).__init__()
        self.model = models.vgg16(pretrained=True)
        for param in self.model.features.parameters():
            param.requires_grad = False
        self.model.classifier[6] = nn.Linear(4096, num_classes)

    def forward(self, x):
        return self.model(x)


class DataProcessor:
    def __init__(self, dataset_dir, image_size):
        self.dataset_dir = dataset_dir
        self.image_size = image_size

    def get_transform(self):
        return transforms.Compose(
            [
                transforms.Resize(self.image_size),
                transforms.ToTensor(),
            ]
        )

    def load_data(self):
        transform = self.get_transform()
        dataset = ImageFolder(self.dataset_dir, transform=transform)
        train_size = int(0.8 * len(dataset))
        val_test_size = len(dataset) - train_size
        val_size = int(0.1 * len(dataset))
        test_size = val_test_size - val_size
        train_data, val_data, test_data = random_split(
            dataset, [train_size, val_size, test_size]
        )
        train_loader = DataLoader(train_data, batch_size=64, shuffle=True)
        val_loader = DataLoader(val_data, batch_size=64, shuffle=True)
        test_loader = DataLoader(test_data, batch_size=64, shuffle=True)
        return train_loader, val_loader, test_loader


class ModelTrainer:
    def __init__(
        self, model, metrics_manager, device="cpu", learning_rate=0.001, epochs=5
    ):
        self.model = model.to(device)
        self.device = device
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = nn.CrossEntropyLoss()
        self.epochs = epochs
        self.metrics_manager = metrics_manager

    def train(self, train_loader, val_loader):
        for epoch in range(self.epochs):
            self.model.train()
            train_losses = []
            all_preds, all_labels = [], []
            for inputs, labels in train_loader:
                inputs, labels = inputs.to(self.device), labels.to(self.device)
                self.optimizer.zero_grad()
                outputs = self.model(inputs)
                loss = self.criterion(outputs, labels)
                loss.backward()
                self.optimizer.step()
                train_losses.append(loss.item())
                _, preds = torch.max(outputs, 1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

            train_accuracy = accuracy_score(all_labels, all_preds)
            train_precision = precision_score(
                all_labels, all_preds, average="macro", zero_division=0
            )
            train_recall = recall_score(
                all_labels, all_preds, average="macro", zero_division=0
            )
            train_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
            average_loss = sum(train_losses) / len(train_losses)

            # Record training metrics
            self.metrics_manager.log(
                epoch + 1,
                average_loss,
                train_accuracy,
                train_precision,
                train_recall,
                train_f1,
                "train",
            )

            # Evaluate on validation set
            self.evaluate(val_loader, epoch)

    def evaluate(self, val_loader, epoch):
        self.model.eval()
        val_losses = []
        all_preds, all_labels = [], []
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(self.device), labels.to(self.device)
                outputs = self.model(inputs)
                loss = self.criterion(outputs, labels)
                val_losses.append(loss.item())
                _, preds = torch.max(outputs.data, 1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

            val_accuracy = accuracy_score(all_labels, all_preds)
            val_precision = precision_score(
                all_labels, all_preds, average="macro", zero_division=0
            )
            val_recall = recall_score(
                all_labels, all_preds, average="macro", zero_division=0
            )
            val_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
            average_loss = sum(val_losses) / len(val_losses)

            # Record validation metrics
            self.metrics_manager.log(
                epoch + 1,
                average_loss,
                val_accuracy,
                val_precision,
                val_recall,
                val_f1,
                "validate",
            )

    def test(self, test_loader):
        self.model.eval()
        test_losses = []
        all_preds, all_labels = [], []
        with torch.no_grad():
            for inputs, labels in test_loader:
                inputs, labels = inputs.to(self.device), labels.to(self.device)
                outputs = self.model(inputs)
                loss = self.criterion(outputs, labels)
                test_losses.append(loss.item())
                _, preds = torch.max(outputs.data, 1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

            test_accuracy = accuracy_score(all_labels, all_preds)
            test_precision = precision_score(
                all_labels, all_preds, average="macro", zero_division=0
            )
            test_recall = recall_score(
                all_labels, all_preds, average="macro", zero_division=0
            )
            test_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)
            average_loss = sum(test_losses) / len(test_losses)

            # Print test results
            print(
                f"Test Loss: {average_loss}, Test Accuracy: {test_accuracy}, Test Precision: {test_precision}, Test Recall: {test_recall}, Test F1: {test_f1}"
            )


class MetricsManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.metrics = []

    def log(self, epoch, loss, accuracy, precision, recall, f1_score, phase):
        self.metrics.append(
            {
                "epoch": epoch,
                "phase": phase,
                "loss": loss,
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score,
            }
        )

    def save_to_csv(self):
        with open(self.file_path, "w", newline="") as file:
            fieldnames = [
                "epoch",
                "phase",
                "loss",
                "accuracy",
                "precision",
                "recall",
                "f1_score",
            ]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for metric in self.metrics:
                writer.writerow(metric)


# Example usage
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
data_processor = DataProcessor("path/to/dataset", (224, 224))
train_loader, val_loader, test_loader = data_processor.load_data()

metrics_manager = MetricsManager("metrics.csv")
model = BasicCNN(num_classes=10)  # or CustomVGG16(num_classes=25)
trainer = ModelTrainer(
    model, metrics_manager, device=device, learning_rate=0.001, epochs=10
)

trainer.train(train_loader, val_loader)
trainer.test(test_loader)
metrics_manager.save_to_csv()

# Example usage of the EnhancedLeNet
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = EnhancedLeNet(num_classes=10).to(device)

# Assuming you have a hypothetical `train_loader` and `val_loader`
# and MetricsManager and ModelTrainer classes are defined as before

# metrics_manager = MetricsManager('metrics.csv')
# trainer = ModelTrainer(model, metrics_manager, device=device, learning_rate=0.001, epochs=10)
# trainer.train(train_loader, val_loader)
# metrics_manager.save_to_csv()
