import os
import time

import torch
import torchvision.models as models
import torchvision.transforms as transforms
from torch.utils.data import DataLoader, random_split
from torchinfo import summary
from torchvision.datasets import ImageFolder
from tqdm.auto import tqdm


class VGG16:
    def __init__(self, batch_size, learning_rate):
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def loadData(self, input_path):
        """
        Load data from input path.
        """
        tf = transforms.Compose([transforms.ToTensor()])
        self.input_data = ImageFolder(input_path, transform=tf)

    def splitTrainData(self, train_ratio):
        """
        Split data into training and validation sets.
        """
        train_size = int(train_ratio * len(self.input_data))
        val_size = len(self.input_data) - train_size
        train_data, valid_data = random_split(self.input_data, [train_size, val_size])

        # set data loader
        self.train_loader = DataLoader(
            train_data, batch_size=self.batch_size, shuffle=True
        )
        self.valid_loader = DataLoader(
            valid_data, batch_size=self.batch_size, shuffle=True
        )

    def setValidationData(self):
        """
        Set validation data.
        """
        self.valid_loader = DataLoader(
            self.input_data, batch_size=self.batch_size, shuffle=True
        )

    def loadModel(self, pretrained: str = None):
        """
        Load VGG16 model.
        """
        # set model
        self.model = models.vgg16(weights=models.VGG16_Weights.DEFAULT).to(self.device)

        # fine tune: customize model classifier
        self.model.classifier[0] = torch.nn.Linear(
            in_features=25088, out_features=2048, bias=True
        )
        self.model.classifier[3] = torch.nn.Linear(
            in_features=2048, out_features=2048, bias=True
        )
        self.model.classifier[6] = torch.nn.Linear(
            in_features=2048, out_features=25, bias=True
        )

        # frozen layers, set requires_grad to False, so that the parameters will not be updated during training
        for param in self.model.parameters():
            param.requires_grad_(False)

        # unfrozen layers, set requires_grad to True, so that the parameters will be updated during training
        self.model.features[24].requires_grad_(True)
        self.model.features[26].requires_grad_(True)
        self.model.features[28].requires_grad_(True)
        self.model.classifier[0].requires_grad_(True)
        self.model.classifier[3].requires_grad_(True)
        self.model.classifier[6].requires_grad_(True)

        # set optimizer and loss function
        self.optimizer = torch.optim.SGD(self.model.parameters(), lr=self.learning_rate)
        self.criterion = torch.nn.CrossEntropyLoss()

        # load pretrained model
        if pretrained is not None:
            checkpoint = torch.load(pretrained)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            self.criterion.load_state_dict(checkpoint["loss"])
            self.model.eval()

        summary(self.model, input_size=(self.batch_size, 3, 224, 224))

    def trainModel(self, epochs, checkpoint_path: str = None, log_path=None):
        """
        Train the model.
        """
        train_losses, test_losses = [], []
        train_acc, test_acc = [], []
        if checkpoint_path is not None:
            os.makedirs(checkpoint_path, exist_ok=True)
        for epoch in range(epochs):
            start_time = time.time()
            iter, iter2 = 0, 0  # iteration count, used to calculate the average loss
            correct_train, total_train = 0, 0
            correct_test, total_test = 0, 0
            train_loss, test_loss = 0.0, 0.0

            self.model.train()  # set the model to training mode
            print("epoch: " + str(epoch + 1) + " / " + str(epochs))

            # ---------------------------
            # Training Stage
            # ---------------------------
            for x, label in tqdm(self.train_loader, ncols=50):
                x, label = x.to(self.device), label.to(self.device)
                self.optimizer.zero_grad()  # clear the gradients of all optimized variables
                train_output = self.model(
                    x
                )  # forward pass: compute predicted outputs by passing inputs to the model
                train_loss_c = self.criterion(
                    train_output, label
                )  # calculate the batch loss
                train_loss_c.backward()  # backward pass: compute gradient of the loss with respect to model parameters
                self.optimizer.step()  # perform a single optimization step (parameter update)

                # calculate training accuracy (correct_train / total_train)
                _, predicted = torch.max(
                    train_output.data, 1
                )  # get the predicted class
                total_train += label.size(0)  # update the total count
                correct_train += (predicted == label).sum()  # update the correct count
                train_loss += train_loss_c.item()  # update the loss
                iter += 1  # update the iteration count

            print(
                "Training acc: %.3f | loss: %.3f"
                % (correct_train / total_train, train_loss / iter)
            )

            if checkpoint_path is not None:
                self.saveModel(
                    epoch, checkpoint_path + "/epoch_" + str(epoch + 1) + ".pth"
                )

            # --------------------------
            # Testing Stage
            # --------------------------
            self.model.eval()  # set the model to evaluation mode
            for x, label in tqdm(self.valid_loader, ncols=50):
                with torch.no_grad():  # turn off gradients for evaluation
                    x, label = x.to(self.device), label.to(self.device)
                    test_output = self.model(
                        x
                    )  # forward pass: compute predicted outputs by passing inputs to the model
                    test_loss_c = self.criterion(
                        test_output, label
                    )  # calculate the batch loss

                    # calculate testing accuracy (correct_test / total_test)
                    _, predicted = torch.max(test_output.data, 1)
                    total_test += label.size(0)
                    correct_test += (predicted == label).sum()
                    test_loss += test_loss_c.item()
                    iter2 += 1

            print(
                "Testing acc: %.3f | loss: %.3f"
                % (correct_test / total_test, test_loss / iter2)
            )

            train_acc.append(
                100 * (correct_train / total_train).cpu()
            )  # training accuracy
            test_acc.append(100 * (correct_test / total_test).cpu())  # testing accuracy
            train_losses.append((train_loss / iter))  # train loss
            test_losses.append((test_loss / iter2))  # test loss

            end_time = time.time()
            print("Cost %.3f(secs)" % (end_time - start_time))

            if log_path is not None:
                with open(log_path, "a") as f:
                    f.write("epoch: " + str(epoch + 1) + " / " + str(epochs) + "\n")
                    f.write(
                        "Training acc: %.3f | loss: %.3f"
                        % (correct_train / total_train, train_loss / iter)
                        + "\n"
                    )
                    f.write(
                        "Testing acc: %.3f | loss: %.3f"
                        % (correct_test / total_test, test_loss / iter2)
                        + "\n"
                    )
                    f.write("Cost %.3f(secs)" % (end_time - start_time) + "\n" + "\n")

        return train_acc, test_acc, train_losses, test_losses

    def saveModel(self, epoch, checkpoint_path):
        """
        Save the model.
        """
        # torch.save(self.model.state_dict(), save_model_path)
        torch.save(
            {
                "epoch": epoch,
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "loss": self.criterion.state_dict(),
            },
            checkpoint_path,
        )

    def validateModel(self):
        """
        Validate the model.
        """
        self.model.eval()  # set the model to evaluation mode
        total_test = 0
        correct_test = 0
        test_loss = 0.0
        iter2 = 0
        for x, label in tqdm(self.valid_loader, ncols=50):
            with torch.no_grad():  # turn off gradients for evaluation
                x, label = x.to(self.device), label.to(self.device)
                test_output = self.model(
                    x
                )  # forward pass: compute predicted outputs by passing inputs to the model
                test_loss_c = self.criterion(
                    test_output, label
                )  # calculate the batch loss

                # calculate testing accuracy (correct_test / total_test)
                _, predicted = torch.max(test_output.data, 1)
                total_test += label.size(0)
                correct_test += (predicted == label).sum()
                test_loss += test_loss_c.item()
                iter2 += 1

        print(
            "Testing acc: %.3f | loss: %.3f"
            % (correct_test / total_test, test_loss / iter2)
        )
