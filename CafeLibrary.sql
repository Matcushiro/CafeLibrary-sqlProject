CREATE DATABASE CafeLibrary;
GO
USE CafeLibrary;
GO

/* Таблицы */
-- Авторы книг
CREATE TABLE Authors
(
    AuthorID    INT IDENTITY(1,1) PRIMARY KEY,
    FirstName   NVARCHAR(50)  NOT NULL,
    LastName    NVARCHAR(50)  NOT NULL,
    BirthYear   SMALLINT      NOT NULL,
    DeathYear   SMALLINT      NULL,
    CONSTRAINT CK_Authors_Years CHECK (DeathYear IS NULL OR DeathYear > BirthYear)
);
GO

-- Сотрудники
CREATE TABLE Employees
(
    EmployeeID        INT IDENTITY(1,1) PRIMARY KEY,
    FullName          NVARCHAR(150) NOT NULL,
    SalaryCardNumber  VARCHAR(20)   NOT NULL,
    Phone             VARCHAR(20)   NOT NULL,
    ProcessedOrders   INT NOT NULL DEFAULT 0,
    Salary            DECIMAL(10,2) NOT NULL,
    IsStaff           BIT NOT NULL DEFAULT 1,
    CONSTRAINT CK_Employees_Salary CHECK (Salary >= 0)
);
GO

-- Клиенты
CREATE TABLE Clients
(
    ClientID        INT IDENTITY(1,1) PRIMARY KEY,
    LastName        NVARCHAR(50) NOT NULL,
    FirstName       NVARCHAR(50) NOT NULL,
    PaymentMethod   NVARCHAR(10) NOT NULL,          -- Карта / Наличные
    CardNumber      VARCHAR(20)  NULL,
    EmployeeID      INT NULL,                       -- Кто обслуживает
    CONSTRAINT CK_Clients_PaymentMethod CHECK (PaymentMethod IN (N'Карта', N'Наличные')),
    CONSTRAINT CK_Clients_CardConsistency CHECK (
        (PaymentMethod = N'Карта'    AND CardNumber IS NOT NULL) OR
        (PaymentMethod = N'Наличные' AND CardNumber IS NULL)
    ),
    CONSTRAINT FK_Clients_Employees FOREIGN KEY (EmployeeID)
        REFERENCES Employees(EmployeeID) ON DELETE SET NULL
);
GO

-- Книги
CREATE TABLE Books
(
    BookID       INT IDENTITY(1,1) PRIMARY KEY,
    Title        NVARCHAR(200) NOT NULL,
    WrittenDate  DATE NOT NULL,
    AuthorID     INT NOT NULL,
    IsBorrowed   BIT NOT NULL DEFAULT 0,
    ClientID     INT NULL,
    CONSTRAINT FK_Books_Authors FOREIGN KEY (AuthorID)
        REFERENCES Authors(AuthorID) ON DELETE CASCADE,
    CONSTRAINT FK_Books_Clients FOREIGN KEY (ClientID)
        REFERENCES Clients(ClientID) ON DELETE SET NULL,
    CONSTRAINT CK_Books_BorrowConsistency CHECK (
        (IsBorrowed = 0 AND ClientID IS NULL) OR
        (IsBorrowed = 1 AND ClientID IS NOT NULL)
    )
);
GO

-- Меню
CREATE TABLE MenuItems
(
    ItemID       INT IDENTITY(1,1) PRIMARY KEY,
    Name         NVARCHAR(100) NOT NULL,
    Ingredients  NVARCHAR(500) NOT NULL,
    Cost         DECIMAL(10,2) NOT NULL,
    Profit       DECIMAL(10,2) NOT NULL,
    CONSTRAINT CK_MenuItems_Cost CHECK (Cost >= 0),
    CONSTRAINT CK_MenuItems_Profit CHECK (Profit >= 0 AND Profit <= Cost)
);
GO

-- Заказы (шапка)
CREATE TABLE Orders
(
    OrderID      INT IDENTITY(1,1) PRIMARY KEY,
    ClientID     INT NOT NULL,
    OrderDate    DATETIME NOT NULL DEFAULT GETDATE(),
    TotalCost    DECIMAL(10,2) NOT NULL DEFAULT 0,
    IsCard       BIT NOT NULL,
    CardNumber   VARCHAR(20) NULL,
    EmployeeID   INT NOT NULL,
    CONSTRAINT FK_Orders_Clients FOREIGN KEY (ClientID)
        REFERENCES Clients(ClientID) ON DELETE CASCADE,
    CONSTRAINT FK_Orders_Employees FOREIGN KEY (EmployeeID)
        REFERENCES Employees(EmployeeID),
    CONSTRAINT CK_Orders_CardConsistency CHECK (
        (IsCard = 1 AND CardNumber IS NOT NULL) OR
        (IsCard = 0 AND CardNumber IS NULL)
    ),
    CONSTRAINT CK_Orders_TotalCost CHECK (TotalCost >= 0)
);
GO

-- Позиции заказа
CREATE TABLE OrderItems
(
    OrderItemID  INT IDENTITY(1,1) PRIMARY KEY,
    OrderID      INT NOT NULL,
    ItemID       INT NOT NULL,
    Quantity     INT NOT NULL DEFAULT 1,
    PriceAtOrder DECIMAL(10,2) NOT NULL,
    CONSTRAINT FK_OrderItems_Orders FOREIGN KEY (OrderID)
        REFERENCES Orders(OrderID) ON DELETE CASCADE,
    CONSTRAINT FK_OrderItems_MenuItems FOREIGN KEY (ItemID)
        REFERENCES MenuItems(ItemID),
    CONSTRAINT CK_OrderItems_Quantity CHECK (Quantity > 0)
);
GO

/* Триггеры */
-- Пересчёт суммы заказа при изменении его позиций
CREATE TRIGGER trg_OrderItems_UpdateTotal
ON OrderItems
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    ;WITH AffectedOrders AS (
        SELECT OrderID FROM inserted
        UNION
        SELECT OrderID FROM deleted
    )
    UPDATE o
    SET o.TotalCost = ISNULL((
        SELECT SUM(oi.Quantity * oi.PriceAtOrder)
        FROM OrderItems oi WHERE oi.OrderID = o.OrderID
    ), 0)
    FROM Orders o
    JOIN AffectedOrders ao ON ao.OrderID = o.OrderID;
END;
GO

-- Увеличение счётчика обработанных заказов у сотрудника
CREATE TRIGGER trg_Orders_IncrementEmployeeCounter
ON Orders
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE e
    SET e.ProcessedOrders = e.ProcessedOrders + 1
    FROM Employees e
    JOIN inserted i ON i.EmployeeID = e.EmployeeID;
END;
GO

/* Представления */

CREATE VIEW vw_AuthorsWithBooks AS
SELECT
    a.AuthorID, a.FirstName, a.LastName, a.BirthYear, a.DeathYear,
    STRING_AGG(CAST(b.BookID AS NVARCHAR(10)), ',') AS BookIDs,
    STRING_AGG(b.Title, ', ') AS BookTitles
FROM Authors a
LEFT JOIN Books b ON b.AuthorID = a.AuthorID
GROUP BY a.AuthorID, a.FirstName, a.LastName, a.BirthYear, a.DeathYear;
GO

CREATE VIEW vw_BooksFull AS
SELECT
    b.BookID, b.Title, b.WrittenDate, a.AuthorID,
    a.FirstName + ' ' + a.LastName AS AuthorFullName,
    b.IsBorrowed, b.ClientID,
    c.LastName + ' ' + c.FirstName AS ClientFullName
FROM Books b
JOIN Authors a ON a.AuthorID = b.AuthorID
LEFT JOIN Clients c ON c.ClientID = b.ClientID;
GO

CREATE VIEW vw_OrdersFull AS
SELECT
    o.OrderID, o.ClientID,
    cl.LastName + ' ' + cl.FirstName AS ClientFullName,
    o.OrderDate, o.TotalCost, o.IsCard, o.CardNumber,
    o.EmployeeID, e.FullName AS EmployeeFullName,
    STRING_AGG(CAST(mi.ItemID AS NVARCHAR(10)), ',') AS ItemIDs,
    STRING_AGG(mi.Name + ' x' + CAST(oi.Quantity AS NVARCHAR(5)), ', ') AS ItemNames
FROM Orders o
JOIN Clients cl ON cl.ClientID = o.ClientID
JOIN Employees e ON e.EmployeeID = o.EmployeeID
LEFT JOIN OrderItems oi ON oi.OrderID = o.OrderID
LEFT JOIN MenuItems mi ON mi.ItemID = oi.ItemID
GROUP BY o.OrderID, o.ClientID, cl.LastName, cl.FirstName, o.OrderDate,
         o.TotalCost, o.IsCard, o.CardNumber, o.EmployeeID, e.FullName;
GO

CREATE VIEW vw_ClientsFull AS
SELECT
    c.ClientID, c.LastName, c.FirstName, c.PaymentMethod, c.CardNumber, c.EmployeeID,
    STRING_AGG(CAST(o.OrderID AS NVARCHAR(10)), ',') AS OrderIDs,
    SUM(o.TotalCost) AS TotalSpent,
    (SELECT STRING_AGG(CAST(b.BookID AS NVARCHAR(10)), ',') FROM Books b WHERE b.ClientID = c.ClientID) AS BorrowedBookIDs,
    (SELECT STRING_AGG(b.Title, ', ') FROM Books b WHERE b.ClientID = c.ClientID) AS BorrowedBookTitles
FROM Clients c
LEFT JOIN Orders o ON o.ClientID = c.ClientID
GROUP BY c.ClientID, c.LastName, c.FirstName, c.PaymentMethod, c.CardNumber, c.EmployeeID;
GO

/* Поиск */
-- Найти запись по ID в указанной таблице
CREATE PROCEDURE sp_FindById
    @TableName NVARCHAR(50),
    @ID        INT
AS
BEGIN
    SET NOCOUNT ON;
    IF @TableName = 'Books'       SELECT * FROM vw_BooksFull WHERE BookID = @ID;
    ELSE IF @TableName = 'Authors'    SELECT * FROM vw_AuthorsWithBooks WHERE AuthorID = @ID;
    ELSE IF @TableName = 'Clients'    SELECT * FROM vw_ClientsFull WHERE ClientID = @ID;
    ELSE IF @TableName = 'MenuItems'  SELECT * FROM MenuItems WHERE ItemID = @ID;
    ELSE IF @TableName = 'Orders'     SELECT * FROM vw_OrdersFull WHERE OrderID = @ID;
    ELSE IF @TableName = 'Employees'  SELECT * FROM Employees WHERE EmployeeID = @ID;
    ELSE RAISERROR(N'Неизвестное имя таблицы', 16, 1);
END;
GO

-- Поиск текста по всем таблицам сразу (с указанием источника)
CREATE PROCEDURE sp_SearchByName
    @SearchText NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Pattern NVARCHAR(102) = '%' + @SearchText + '%';

    SELECT N'Книги' AS ИсточникТаблицы, BookID AS ID, Title AS Название
    FROM Books WHERE Title LIKE @Pattern
    UNION ALL
    SELECT N'Авторы', AuthorID, FirstName + ' ' + LastName
    FROM Authors WHERE FirstName LIKE @Pattern OR LastName LIKE @Pattern
    UNION ALL
    SELECT N'Клиенты', ClientID, LastName + ' ' + FirstName
    FROM Clients WHERE LastName LIKE @Pattern OR FirstName LIKE @Pattern
    UNION ALL
    SELECT N'Меню', ItemID, Name
    FROM MenuItems WHERE Name LIKE @Pattern
    UNION ALL
    SELECT N'Сотрудники', EmployeeID, FullName
    FROM Employees WHERE FullName LIKE @Pattern;
END;
GO

/* Выдача/возврат книг */

CREATE PROCEDURE sp_IssueBook
    @BookID   INT,
    @ClientID INT
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM Books WHERE BookID = @BookID)
    BEGIN RAISERROR(N'Книга не найдена', 16, 1); RETURN; END

    IF EXISTS (SELECT 1 FROM Books WHERE BookID = @BookID AND IsBorrowed = 1)
    BEGIN RAISERROR(N'Книга уже выдана', 16, 1); RETURN; END

    IF NOT EXISTS (SELECT 1 FROM Clients WHERE ClientID = @ClientID)
    BEGIN RAISERROR(N'Клиент не найден', 16, 1); RETURN; END

    UPDATE Books SET IsBorrowed = 1, ClientID = @ClientID WHERE BookID = @BookID;
END;
GO

CREATE PROCEDURE sp_ReturnBook
    @BookID INT
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM Books WHERE BookID = @BookID AND IsBorrowed = 1)
    BEGIN RAISERROR(N'Эта книга не выдана', 16, 1); RETURN; END

    UPDATE Books SET IsBorrowed = 0, ClientID = NULL WHERE BookID = @BookID;
END;
GO

/* Заказы */
-- Создать заказ, вернуть новый ID результатом SELECT
CREATE PROCEDURE sp_CreateOrder
    @ClientID    INT,
    @EmployeeID  INT,
    @IsCard      BIT,
    @CardNumber  VARCHAR(20) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM Clients WHERE ClientID = @ClientID)
    BEGIN RAISERROR(N'Клиент не найден', 16, 1); RETURN; END

    IF NOT EXISTS (SELECT 1 FROM Employees WHERE EmployeeID = @EmployeeID)
    BEGIN RAISERROR(N'Сотрудник не найден', 16, 1); RETURN; END

    INSERT INTO Orders (ClientID, EmployeeID, IsCard, CardNumber, TotalCost)
    VALUES (@ClientID, @EmployeeID, @IsCard, @CardNumber, 0);

    SELECT SCOPE_IDENTITY() AS NewOrderID;
END;
GO

CREATE PROCEDURE sp_AddOrderItem
    @OrderID   INT,
    @ItemID    INT,
    @Quantity  INT = 1
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Price DECIMAL(10,2);
    SELECT @Price = Cost FROM MenuItems WHERE ItemID = @ItemID;

    IF @Price IS NULL
    BEGIN RAISERROR(N'Блюдо не найдено', 16, 1); RETURN; END

    IF NOT EXISTS (SELECT 1 FROM Orders WHERE OrderID = @OrderID)
    BEGIN RAISERROR(N'Заказ не найден', 16, 1); RETURN; END

    INSERT INTO OrderItems (OrderID, ItemID, Quantity, PriceAtOrder)
    VALUES (@OrderID, @ItemID, @Quantity, @Price);
END;
GO

/* CRUDы (Create Read Update Delete) */
/* CRUD Книг */

CREATE PROCEDURE sp_AddBook
    @Title NVARCHAR(200), @WrittenDate DATE, @AuthorID INT
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM Authors WHERE AuthorID = @AuthorID)
    BEGIN RAISERROR(N'Автор не найден', 16, 1); RETURN; END
    INSERT INTO Books (Title, WrittenDate, AuthorID, IsBorrowed)
    VALUES (@Title, @WrittenDate, @AuthorID, 0);
    SELECT SCOPE_IDENTITY() AS NewID;
END;
GO

CREATE PROCEDURE sp_UpdateBook
    @BookID INT, @Title NVARCHAR(200), @WrittenDate DATE, @AuthorID INT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Books SET Title=@Title, WrittenDate=@WrittenDate, AuthorID=@AuthorID
    WHERE BookID=@BookID;
END;
GO

CREATE PROCEDURE sp_DeleteBook
    @BookID INT
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM Books WHERE BookID=@BookID AND IsBorrowed=1)
    BEGIN RAISERROR(N'Нельзя удалить выданную книгу', 16, 1); RETURN; END
    DELETE FROM Books WHERE BookID=@BookID;
END;
GO

/* CRUD Авторов */

CREATE PROCEDURE sp_AddAuthor
    @FirstName NVARCHAR(50), @LastName NVARCHAR(50), @BirthYear SMALLINT, @DeathYear SMALLINT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO Authors (FirstName, LastName, BirthYear, DeathYear)
    VALUES (@FirstName, @LastName, @BirthYear, @DeathYear);
    SELECT SCOPE_IDENTITY() AS NewID;
END;
GO

CREATE PROCEDURE sp_UpdateAuthor
    @AuthorID INT, @FirstName NVARCHAR(50), @LastName NVARCHAR(50), @BirthYear SMALLINT, @DeathYear SMALLINT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Authors SET FirstName=@FirstName, LastName=@LastName,
           BirthYear=@BirthYear, DeathYear=@DeathYear
    WHERE AuthorID=@AuthorID;
END;
GO

CREATE PROCEDURE sp_DeleteAuthor
    @AuthorID INT
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Authors WHERE AuthorID=@AuthorID; -- книги удалятся каскадно
END;
GO

/* CRUD Клиентов */

CREATE PROCEDURE sp_AddClient
    @LastName NVARCHAR(50), @FirstName NVARCHAR(50),
    @PaymentMethod NVARCHAR(10), @CardNumber VARCHAR(20) = NULL,
    @EmployeeID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO Clients (LastName, FirstName, PaymentMethod, CardNumber, EmployeeID)
    VALUES (@LastName, @FirstName, @PaymentMethod, @CardNumber, @EmployeeID);
    SELECT SCOPE_IDENTITY() AS NewID;
END;
GO

CREATE PROCEDURE sp_UpdateClient
    @ClientID INT, @LastName NVARCHAR(50), @FirstName NVARCHAR(50),
    @PaymentMethod NVARCHAR(10), @CardNumber VARCHAR(20) = NULL,
    @EmployeeID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Clients SET LastName=@LastName, FirstName=@FirstName,
           PaymentMethod=@PaymentMethod, CardNumber=@CardNumber, EmployeeID=@EmployeeID
    WHERE ClientID=@ClientID;
END;
GO

CREATE PROCEDURE sp_DeleteClient
    @ClientID INT
AS
BEGIN
    SET NOCOUNT ON;
    DELETE FROM Clients WHERE ClientID=@ClientID; -- заказы удалятся каскадно
END;
GO

/* CRUD Менюшки */

CREATE PROCEDURE sp_AddMenuItem
    @Name NVARCHAR(100), @Ingredients NVARCHAR(500), @Cost DECIMAL(10,2), @Profit DECIMAL(10,2)
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO MenuItems (Name, Ingredients, Cost, Profit)
    VALUES (@Name, @Ingredients, @Cost, @Profit);
    SELECT SCOPE_IDENTITY() AS NewID;
END;
GO

CREATE PROCEDURE sp_UpdateMenuItem
    @ItemID INT, @Name NVARCHAR(100), @Ingredients NVARCHAR(500), @Cost DECIMAL(10,2), @Profit DECIMAL(10,2)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE MenuItems SET Name=@Name, Ingredients=@Ingredients, Cost=@Cost, Profit=@Profit
    WHERE ItemID=@ItemID;
END;
GO

CREATE PROCEDURE sp_DeleteMenuItem
    @ItemID INT
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM OrderItems WHERE ItemID=@ItemID)
    BEGIN RAISERROR(N'Блюдо встречается в заказах, удаление запрещено', 16, 1); RETURN; END
    DELETE FROM MenuItems WHERE ItemID=@ItemID;
END;
GO

/* CRUD Сотрудников */

CREATE PROCEDURE sp_AddEmployee
    @FullName NVARCHAR(150), @SalaryCardNumber VARCHAR(20), @Phone VARCHAR(20),
    @Salary DECIMAL(10,2), @IsStaff BIT = 1
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO Employees (FullName, SalaryCardNumber, Phone, Salary, IsStaff)
    VALUES (@FullName, @SalaryCardNumber, @Phone, @Salary, @IsStaff);
    SELECT SCOPE_IDENTITY() AS NewID;
END;
GO

CREATE PROCEDURE sp_UpdateEmployee
    @EmployeeID INT, @FullName NVARCHAR(150), @SalaryCardNumber VARCHAR(20),
    @Phone VARCHAR(20), @Salary DECIMAL(10,2), @IsStaff BIT = 1
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Employees SET FullName=@FullName, SalaryCardNumber=@SalaryCardNumber,
           Phone=@Phone, Salary=@Salary, IsStaff=@IsStaff
    WHERE EmployeeID=@EmployeeID;
END;
GO

CREATE PROCEDURE sp_DeleteEmployee
    @EmployeeID INT
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (SELECT 1 FROM Orders WHERE EmployeeID=@EmployeeID)
    BEGIN RAISERROR(N'У сотрудника есть заказы, удаление запрещено', 16, 1); RETURN; END
    DELETE FROM Employees WHERE EmployeeID=@EmployeeID;
END;
GO

PRINT N'База данных CafeLibrary успешно создана.';