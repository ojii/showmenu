(function() {
  'use strict';

  angular.module('showmenu', ['ui.tree']).controller('MainCtrl', function($scope) {
    $scope.from_level = 0;
    $scope.to_level = 100;
    $scope.extra_inactive = 100;
    $scope.extra_active = 100;
    $scope.list = [{
      "id": 1,
      "title": "1. dragon-breath",
      "items": []
    }, {
      "id": 2,
      "title": "2. moiré-vision",
      "items": [{
        "id": 21,
        "title": "2.1. tofu-animation",
        "items": [{
          "id": 211,
          "title": "2.1.1. spooky-giraffe",
          "items": []
        }, {
          "id": 212,
          "title": "2.1.2. bubble-burst",
          "items": []
        }]
      }, {
        "id": 22,
        "title": "2.2. barehand-atomsplitting",
        "items": []
      }]
    }, {
      "id": 3,
      "title": "3. unicorn-zapper",
      "items": []
    }, {
      "id": 4,
      "title": "4. romantic-transclusion",
      "items": []
    }];
    $scope.menu = [];

    $scope.selectedItem = {};

    $scope.options = {};
    $scope.menu_options = {};
    $scope.refreshing = false;

    $scope.remove = function(scope) {
      scope.remove();
    };

    $scope.toggle = function(scope) {
      scope.toggle();
    };

    $scope.newSubItem = function(scope) {
      var nodeData = scope.$modelValue;
      nodeData.items.push({
        id: nodeData.id * 10 + nodeData.items.length,
        title: nodeData.title + '.' + (nodeData.items.length + 1),
        items: []
      });
    };

    $scope.request_new_menu = function(){
      $scope.refreshing = true;
      var request = new XMLHttpRequest();
      var data = {
        'tree': $scope.list,
        'from': $scope.from_level,
        'to': $scope.to_level,
        'extra_inactive': $scope.extra_inactive,
        'extra_active': $scope.extra_active
      };
      request.onreadystatechange = function () {
        if (request.readyState === 4 && request.status === 200) {
          $scope.menu = JSON.parse(request.responseText);
          $scope.$apply();
          $scope.refreshing = false;
        }
      };
      request.open('POST', '/menu/');
      request.setRequestHeader('Content-Type', 'application/json');
      request.send(JSON.stringify(data));
    };
  });
})();
